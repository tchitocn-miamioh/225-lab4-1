
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

        stage('Deploy to Dev Environment') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'tchitocn-225',
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        sed -i \
                          "s|${DOCKER_IMAGE}:latest|${DOCKER_IMAGE}:${IMAGE_TAG}|" \
                          deployment-dev.yaml

                        kubectl apply -f deployment-dev.yaml

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
                        kubectl get deployments -n default
                        kubectl get pods -n default
                        kubectl get svc flask-service -n default
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
