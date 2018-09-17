pipeline {

    agent any


    stages {

      stage('prep') {
        steps {
          timestamps {
            ansiColor('xterm') {
              sh ".ci/init-pyenv"
              sh '.ci/run-pyenv invoke destroy'
              sh ".ci/run-pyenv invoke prep"
              sh ".ci/run-pyenv invoke ansible-inventory -b default"
            }
          }
        }
      }

      stage('tests') {
        steps {
          timestamps {
            ansiColor('xterm') {
              sh '.ci/run-pyenv invoke test -t --recreate'
            }
          }
        }
      }

    }

    post {
      always {
        sh '.ci/run-pyenv invoke destroy'
      }
    }
}
