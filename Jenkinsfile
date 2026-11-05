
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'threatwatch'
        IMAGE_TAG = '1.0'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out ThreatWatch source code'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    venv/bin/pip install --upgrade pip
                    venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    venv/bin/python -m pytest -v
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                '''
            }
        }

        stage('Verify Docker Image') {
            steps {
                sh '''
                    docker images ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }
    }

    post {
        success {
            echo 'ThreatWatch CI Pipeline completed successfully!'
        }

        failure {
            echo 'ThreatWatch CI Pipeline failed. Check the console output.'
        }
    }
}
