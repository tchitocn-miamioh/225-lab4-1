
pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'roseaw-dockerhub'
        DOCKER_IMAGE = 'cithit/tchitocn'
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        GITHUB_URL = 'https://github.com/tchitocn-miamioh/225-lab4-1.git'
    }

    stages {

        stage('Checkout') {
            steps {
                cleanWs()

                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[url: "${GITHUB_URL}"]]
                ])
            }
        }

        stage('Python Application Tests - Pytest') {
            steps {
                script {
                    docker.image('python:3.9-slim').inside('-u 0:0') {
                        sh '''
                            python -m pip install --no-cache-dir \
                              -r requirements.txt pytest

                            python -m pytest -v tests/
                        '''
                    }
                }
            }
        }

        stage('Python Security Scan - Bandit') {
            steps {
                script {
                    docker.image('python:3.9-slim').inside('-u 0:0') {
                        sh '''
                            python -m pip install --no-cache-dir bandit

                            bandit -r main.py -ll -ii
                        '''
                    }
                }
            }
        }

        stage('Dependency Security Scan - pip-audit') {
            steps {
                script {
                    docker.image('python:3.9-slim').inside('-u 0:0') {
                        sh '''
                            python -m pip install --no-cache-dir pip-audit

                            python -m pip_audit -r requirements.txt
                        '''
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.withRegistry(
                        'https://registry.hub.docker.com',
                        "${DOCKER_CREDENTIALS_ID}"
                    ) {
                        docker.build("${DOCKER_IMAGE}:${IMAGE_TAG}")
                    }
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry(
                        'https://index.docker.io/v1/',
                        "${DOCKER_CREDENTIALS_ID}"
                    ) {
                        docker.image("${DOCKER_IMAGE}:${IMAGE_TAG}").push()
                    }
                }
            }
        }

        stage('Test Kubernetes Connection') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'tchitocn-225',
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        echo "Checking Kubernetes connection..."

                        kubectl config current-context

                        kubectl cluster-info

                        kubectl get nodes

                        kubectl get pods -n default

                        echo "Kubernetes connection test passed."
                    '''
                }
            }
        }

        stage('Deploy to Dev Environment') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'tchitocn-225',
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        echo "Updating Docker image tag..."

                        sed -i \
                          "s|${DOCKER_IMAGE}:latest|${DOCKER_IMAGE}:${IMAGE_TAG}|" \
                          deployment-dev.yaml

                        echo "Deploying to Kubernetes..."

                        kubectl apply -f deployment-dev.yaml

                        echo "Waiting for Flask deployment..."

                        kubectl rollout status \
                          deployment/flask-deployment \
                          -n default \
                          --timeout=180s
                    '''
                }
            }
        }

        stage('Check Kubernetes Cluster') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'tchitocn-225',
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        echo "Checking Kubernetes deployments..."
                        kubectl get deployments -n default

                        echo "Checking running pods..."
                        kubectl get pods -n default

                        echo "Checking Flask service..."
                        kubectl get svc flask-service -n default

                        echo "Checking deployment image..."
                        kubectl get deployment flask-deployment \
                          -n default \
                          -o jsonpath='{.spec.template.spec.containers[*].image}'

                        echo ""
                    '''
                }
            }
        }
    }

    post {
        success {
            slackSend(
                color: "good",
                message: "Build Completed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
            )
        }

        unstable {
            slackSend(
                color: "warning",
                message: "Build Unstable: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
            )
        }

        failure {
            slackSend(
                color: "danger",
                message: "Build Failed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
            )
        }
    }
}
