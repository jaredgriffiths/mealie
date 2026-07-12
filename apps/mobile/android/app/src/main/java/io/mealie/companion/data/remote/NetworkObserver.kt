package io.mealie.companion.data.remote

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.withContext
import kotlinx.coroutines.launch
import kotlinx.coroutines.GlobalScope
import java.net.HttpURLConnection
import java.net.URL
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NetworkObserver @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    private val _isLANReachable = MutableStateFlow(false)
    val isLANReachable: StateFlow<Boolean> = _isLANReachable

    private var mealieHostUrl: String = "https://192.168.50.107:9925" // Default production Mealie server URL

    private val scope = kotlinx.coroutines.CoroutineScope(Dispatchers.IO + kotlinx.coroutines.SupervisorJob())

    init {
        checkMealieReachability()
        connectivityManager.registerDefaultNetworkCallback(object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                // Trigger connection verify check when network switches
                checkMealieReachability()
            }

            override fun onLost(network: Network) {
                _isLANReachable.value = false
            }
        })
    }

    fun updateMealieHost(newHost: String) {
        mealieHostUrl = newHost
        checkMealieReachability()
    }

    fun checkMealieReachability() {
        // Run network socket checks on Background IO dispatcher
        scope.launch {
            try {
                val url = URL(mealieHostUrl)
                val connection = url.openConnection() as HttpURLConnection
                if (connection is javax.net.ssl.HttpsURLConnection) {
                    val trustAllCerts = arrayOf<javax.net.ssl.TrustManager>(
                        object : javax.net.ssl.X509TrustManager {
                            override fun checkClientTrusted(chain: Array<out java.security.cert.X509Certificate>?, authType: String?) {}
                            override fun checkServerTrusted(chain: Array<out java.security.cert.X509Certificate>?, authType: String?) {}
                            override fun getAcceptedIssuers(): Array<java.security.cert.X509Certificate> = arrayOf()
                        }
                    )
                    val sslContext = javax.net.ssl.SSLContext.getInstance("SSL").apply {
                        init(null, trustAllCerts, java.security.SecureRandom())
                    }
                    connection.sslSocketFactory = sslContext.socketFactory
                    connection.hostnameVerifier = javax.net.ssl.HostnameVerifier { _, _ -> true }
                }
                connection.connectTimeout = 2000
                connection.readTimeout = 2000
                connection.requestMethod = "HEAD"
                val responseCode = connection.responseCode
                // Any response code between 100 and 599 means the server is reachable and active.
                // True connection failures will throw an IOException and be caught in the block.
                _isLANReachable.value = responseCode in 100..599
            } catch (e: Exception) {
                _isLANReachable.value = false
            }
        }
    }
}

