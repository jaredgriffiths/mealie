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

    private var mealieHostUrl: String = "http://10.0.2.2:9925" // Default Android Emulator host IP targeting localhost port 9925

    init {
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
        kotlinx.coroutines.GlobalScope.launch(Dispatchers.IO) {
            try {
                val url = URL(mealieHostUrl)
                val connection = url.openConnection() as HttpURLConnection
                connection.connectTimeout = 2000
                connection.readTimeout = 2000
                connection.requestMethod = "HEAD"
                val responseCode = connection.responseCode
                _isLANReachable.value = (responseCode == HttpURLConnection.HTTP_OK || responseCode == HttpURLConnection.HTTP_UNAUTHORIZED)
            } catch (e: Exception) {
                _isLANReachable.value = false
            }
        }
    }
}
