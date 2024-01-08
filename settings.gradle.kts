pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
        maven {
            url = uri("https://repo.eclipse.org/content/repositories/paho-snapshots/")
        }
        maven {
            url = uri("https://jitpack.io")
        }
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven {
            url = uri("https://repo.eclipse.org/content/repositories/paho-snapshots/")
        }
        maven {
            url = uri("https://jitpack.io")
        }
    }
}

rootProject.name = "IoT-project-Stockholm-University"
include(":app")
