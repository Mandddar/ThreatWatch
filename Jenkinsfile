pipeline {
    agent any

    environment {
        IMAGE_NAME = 'threatwatch'
        IMAGE_TAG = '1.0'
        AWS_REGION = 'ap-south-1'
        ECR_REGISTRY = '461929940012.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_REPOSITORY = 'threatwatch'
        EC2_HOST = '65.1.147.24'
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

                        docker logout ${ECR_REGISTRY}
                    '''
                }
            }
        }

        stage('Deploy to AWS EC2') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ec2-ssh-key',
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        set -e

                        ssh -i "$SSH_KEY" \
                            -o StrictHostKeyChecking=no \
                            "$SSH_USER@${EC2_HOST}" \
                            "IMAGE_TAG=${BUILD_NUMBER} bash -s" <<'REMOTE'

                        set -e

                        ECR_REGISTRY="461929940012.dkr.ecr.ap-south-1.amazonaws.com"
                        ECR_IMAGE="$ECR_REGISTRY/threatwatch:$IMAGE_TAG"

                        echo "Logging in to Amazon ECR..."

                        aws ecr get-login-password --region ap-south-1 | \
                            sudo docker login \
                            --username AWS \
                            --password-stdin "$ECR_REGISTRY"

                        echo "Pulling latest ThreatWatch image..."

                        sudo docker pull "$ECR_IMAGE"

                        echo "Stopping previous ThreatWatch container..."

                        sudo docker stop threatwatch || true
                        sudo docker rm threatwatch || true

                        echo "Starting updated ThreatWatch container..."

                        sudo docker run -d \
                            --name threatwatch \
                            --restart unless-stopped \
                            -p 80:5000 \
                            -v threatwatch-data:/app/data \
                            "$ECR_IMAGE"

                        sudo docker logout "$ECR_REGISTRY"

                        echo "Checking application health..."

                        for i in $(seq 1 12); do
                            if curl -fsS http://localhost/health; then
                                echo "ThreatWatch deployment successful!"
                                exit 0
                            fi

                            sleep 5
                        done

                        echo "ThreatWatch health check failed!"
                        sudo docker logs threatwatch
                        exit 1

                        REMOTE
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'ThreatWatch CI/CD Pipeline completed successfully!'
            echo 'Docker image pushed to Amazon ECR.'
            echo 'Application deployment to AWS EC2 completed.'
        }

        failure {
            echo 'ThreatWatch CI/CD Pipeline failed. Check console output.'
        }
    }
}
