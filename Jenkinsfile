pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/700SAGARIKA/warehousepathfinder.git',
                        credentialsId: 'github-credentials'
                    ]]
                ])
                echo 'Code checked out successfully'
            }
        }

        stage('Verify Files') {
            steps {
                script {
                    sh 'ls -la'
                    sh 'test -f Dockerfile && echo "Dockerfile found"'
                    sh 'test -f docker-compose.yml && echo "docker-compose.yml found"'
                    sh 'test -f requirements.txt && echo "requirements.txt found"'
                    sh 'test -f streamlit_app.py && echo "streamlit_app.py found"'
                }
            }
        }

        stage('Build Status') {
            steps {
                echo 'Pipeline Build Successful!'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
