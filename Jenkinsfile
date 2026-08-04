pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build with Docker Compose') {
            steps {
                script {
                    sh 'docker-compose build'
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    sh 'docker-compose down || true'
                    sh 'docker-compose up -d'
                    sh 'sleep 30'
                    sh 'docker-compose exec -T warehouse-app curl -s http://localhost:8010 > /dev/null || exit 1'
                    sh 'echo "Application is running successfully"'
                }
            }
        }

        stage('Cleanup') {
            steps {
                script {
                    sh 'docker-compose down || true'
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        failure {
            echo 'Pipeline failed!'
        }
        success {
            echo 'Pipeline succeeded!'
        }
    }
}
