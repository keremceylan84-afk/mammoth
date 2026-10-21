plugins {
    id("com.android.application")
}

android {
    namespace = "com.keremceylan.mammoth.watchface"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.keremceylan.mammoth.watchface"
        // Watch Face Format v2 (weather data) requires Wear OS 5 / API 34.
        minSdk = 34
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            // Signed with the debug key so the APK can be sideloaded directly.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}
