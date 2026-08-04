pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "warehouse-path-finder:${BUILD_NUMBER}"
        REGISTRY = "docker.io"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh 'docker build -t ${DOCKER_IMAGE} .'
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    sh 'docker compose down || true'
                    sh 'docker compose up -d'
                    sh 'sleep 30'
                    sh 'docker exec warehouse-path-finder curl -f http://localhost:8010 || exit 1'
                }
            }
        }

        stage('Cleanup') {
            steps {
                script {
                    sh 'docker compose down || true'
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
