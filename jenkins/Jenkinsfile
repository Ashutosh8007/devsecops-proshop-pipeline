pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        SONAR_TOKEN = credentials('sonarcloud-token')
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        stage('Install Backend Dependencies') {
            steps {
                sh 'npm install --omit=dev'
            }
        }

        stage('Install Frontend Dependencies') {
            steps {
                dir('frontend') {
                    sh 'npm install'
                }
            }
        }

        stage('SonarCloud Analysis') {
            steps {
                withSonarQubeEnv('SonarCloud') {
                    sh '''
                        npx sonar-scanner \
                        -Dsonar.organization=ashutosh8007 \
                        -Dsonar.projectKey=Ashutosh8007_devsecops-proshop-pipeline \
                        -Dsonar.sources=. \
                        -Dsonar.host.url=https://sonarcloud.io \
                        -Dsonar.token=$SONAR_TOKEN
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                script {
                    def qualityGateStatus = sh(
                        script: '''
                            sleep 10
                            curl -s -u $SONAR_TOKEN: \
                            "https://sonarcloud.io/api/qualitygates/project_status?projectKey=Ashutosh8007_devsecops-proshop-pipeline" \
                            | grep -o '"status":"[A-Z]*"' | head -1 | cut -d'"' -f4
                        ''',
                        returnStdout: true
                    ).trim()

                    echo "SonarCloud Quality Gate status: ${qualityGateStatus}"

                    if (qualityGateStatus != 'OK') {
                        error "Quality Gate failed with status: ${qualityGateStatus}"
                    }
                }
            }
        }

        stage('Build Backend Image') {
            steps {
                sh 'docker build -t $DOCKERHUB_CREDENTIALS_USR/proshop-backend:$IMAGE_TAG .'
            }
        }

        stage('Push Backend Image') {
            steps {
                sh '''
                    echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin
                    docker push $DOCKERHUB_CREDENTIALS_USR/proshop-backend:$IMAGE_TAG
                    docker tag $DOCKERHUB_CREDENTIALS_USR/proshop-backend:$IMAGE_TAG $DOCKERHUB_CREDENTIALS_USR/proshop-backend:latest
                    docker push $DOCKERHUB_CREDENTIALS_USR/proshop-backend:latest
                '''
            }
        }

        stage('Build Frontend Image') {
            steps {
                dir('frontend') {
                    sh 'docker build -t $DOCKERHUB_CREDENTIALS_USR/proshop-frontend:$IMAGE_TAG .'
                }
            }
        }

        stage('Push Frontend Image') {
            steps {
                sh '''
                    docker push $DOCKERHUB_CREDENTIALS_USR/proshop-frontend:$IMAGE_TAG
                    docker tag $DOCKERHUB_CREDENTIALS_USR/proshop-frontend:$IMAGE_TAG $DOCKERHUB_CREDENTIALS_USR/proshop-frontend:latest
                    docker push $DOCKERHUB_CREDENTIALS_USR/proshop-frontend:latest
                '''
            }
        }

        stage('Trivy Scan - Backend') {
            steps {
                sh '''
                    trivy image --severity CRITICAL --exit-code 1 --format table $DOCKERHUB_CREDENTIALS_USR/proshop-backend:$IMAGE_TAG || true
                    trivy image --format table $DOCKERHUB_CREDENTIALS_USR/proshop-backend:$IMAGE_TAG > trivy-backend-report.txt
                '''
                archiveArtifacts artifacts: 'trivy-backend-report.txt', allowEmptyArchive: true
            }
        }

        stage('Trivy Scan - Frontend') {
            steps {
                sh '''
                    trivy image --severity CRITICAL --exit-code 1 --format table $DOCKERHUB_CREDENTIALS_USR/proshop-frontend:$IMAGE_TAG || true
                    trivy image --format table $DOCKERHUB_CREDENTIALS_USR/proshop-frontend:$IMAGE_TAG > trivy-frontend-report.txt
                '''
                archiveArtifacts artifacts: 'trivy-frontend-report.txt', allowEmptyArchive: true
            }
        }

    }

    post {
        always {
            echo 'Pipeline finished.'
        }
        success {
            echo 'Build succeeded!'
        }
        failure {
            echo 'Build failed — check logs above.'
        }
    }
}