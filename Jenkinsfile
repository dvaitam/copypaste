pipeline {
    agent any
    environment {
        GIT_REF = sh(script: '''
            if [ -n "$GIT_REF" ]; then
                echo "$GIT_REF" | sed 's#refs/tags/##' | sed 's#refs/heads/##'
            elif [ -n "$GIT_COMMIT" ]; then
                echo "$GIT_COMMIT"
            else
                echo "main"
            fi
        ''', returnStdout: true).trim()
        VENV_PATH = '/var/lib/jenkins/app'
    }
    stages {
        stage('Deploy') {
            steps {
                dir('/var/lib/jenkins/copypaste') {
                    sh 'git pull origin main'
                    sh "source ${VENV_PATH}/bin/activate && pip install -r requirements.txt && deactivate"
                    sh '/bin/systemctl restart copypaste'
                }
            }
        }
    }
}
