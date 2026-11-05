
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'threatwatch'
        IMAGE_TAG = '1.0'
        AWS_REGION = 'ap-south-1'
        ECR_REGISTRY = '461929940012.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_REPOSITORY = 'threatwatch'
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

        stage('Push Image to Amazon ECR') {
            steps {
                withCredentials([
                    string(credentialsId: 'aws-access-key-id',
                           variable: 'AWS_ACCESS_KEY_ID'),
                    string(credentialsId: 'aws-secret-access-key',
                           variable: 'AWS_SECRET_ACCESS_KEY')
                ]) {
                    sh '''
                        set +x

                        export AWS_DEFAULT_REGION=${AWS_REGION}

                        aws ecr get-login-password \
                            --region ${AWS_REGION} | \
                            docker login \
                            --username AWS \
                            --password-stdin ${ECR_REGISTRY}

                        docker tag ${IMAGE_NAME}:${IMAGE_TAG} \
                            ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}

                        docker tag ${IMAGE_NAME}:${IMAGE_TAG} \
                            ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest

                        docker tag ${IMAGE_NAME}:${IMAGE_TAG} \
                            ${ECR_REGISTRY}/${ECR_REPOSITORY}:${BUILD_NUMBER}

                        docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}
                        docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest
                        docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:${BUILD_NUMBER}
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'ThreatWatch CI Pipeline completed successfully!'
            echo 'Docker image pushed to Amazon ECR.'
        }

        failure {
            echo 'ThreatWatch CI/CD Pipeline failed. Check console output.'
        }
    }
}

