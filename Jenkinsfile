pipeline {
  agent any
  stages {
    stage('Get Source Code') {
      steps {
        git(url: 'https://github.com/plasticruler/tbot.git', branch: 'master')
      }
    }
  }
}