pipeline {
    agent any

    environment {
        SNYK_PATH = '/var/jenkins_home/bin/snyk'
        SNYK_TOKEN = credentials('snyk-token')
        DOCKER_IMAGE = 'vulnerable-python-app'
        DOCKER_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Snyk') {
            steps {
                sh '''
                    if [ ! -x "$SNYK_PATH" ]; then
                        echo "Installing Snyk CLI..."
                        curl -Lo /tmp/snyk https://downloads.snyk.io/cli/stable/snyk-linux-arm64
                        chmod +x /tmp/snyk
                        mkdir -p /var/jenkins_home/bin
                        mv /tmp/snyk /var/jenkins_home/bin/snyk
                        chmod +x /var/jenkins_home/bin/snyk
                    fi

                    ${SNYK_PATH} auth ${SNYK_TOKEN}
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    echo "Building Docker image..."
                    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                '''
            }
        }

        stage('Run Unit Tests') {
            steps {
                sh '''
                    echo "Running unit tests..."
                    docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} python test_app.py
                '''
            }
        }

        stage('Snyk Security Scan - Dependencies') {
            steps {
                script {
                    sh '''
                        echo "Scanning Python dependencies..."
                        mkdir -p reports

                        if [ -f requirements.txt ]; then
                            echo "requirements.txt found"
                            cat requirements.txt
                        fi

                        ${SNYK_PATH} test --file=./requirements.txt --package-manager=pip --json > reports/snyk-deps-report.json || true

                        echo "=== Dependency Scan Results ==="
                        ${SNYK_PATH} test --file=./requirements.txt --package-manager=pip || true
                    '''

                    def hasCritical = sh(
                        script: 'test -s reports/snyk-deps-report.json && grep -q "\\"severity\\":\\"critical\\"" reports/snyk-deps-report.json',
                        returnStatus: true
                    )

                    if (hasCritical == 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo "WARNING: Critical vulnerabilities found in dependencies"
                    }
                }
            }
        }

        stage('Snyk Security Scan - Docker Image') {
            steps {
                script {
                    sh '''
                        echo "Scanning Docker image..."
                        ${SNYK_PATH} container test ${DOCKER_IMAGE}:${DOCKER_TAG} --json > reports/snyk-container-report.json || true

                        echo "=== Container Scan Results ==="
                        ${SNYK_PATH} container test ${DOCKER_IMAGE}:${DOCKER_TAG} || true
                    '''

                    def hasVulnerabilities = sh(
                        script: 'test -s reports/snyk-container-report.json && grep -q "vulnerabilities" reports/snyk-container-report.json',
                        returnStatus: true
                    )

                    if (hasVulnerabilities == 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo "WARNING: Vulnerabilities found in container image"
                    }
                }
            }
        }

        stage('Snyk Code Analysis') {
            steps {
                script {
                    sh '''
                        echo "Running static code analysis..."
                        ${SNYK_PATH} code test --json > reports/snyk-code-report.json || true

                        echo "=== Code Analysis Results ==="
                        ${SNYK_PATH} code test || true
                    '''

                    def hasIssues = sh(
                        script: 'test -s reports/snyk-code-report.json',
                        returnStatus: true
                    )

                    if (hasIssues == 0) {
                        echo "Code quality issues detected"
                    }
                }
            }
        }

        stage('Generate Security Report') {
            steps {
                sh '''
                    echo "Generating consolidated security report..."

                    cat > reports/security-summary.txt << EOF
=== Security Scan Summary ===
Build Number: ${BUILD_NUMBER}
Date: $(date)
Image: ${DOCKER_IMAGE}:${DOCKER_TAG}
EOF

                    if [ -f reports/snyk-deps-report.json ]; then
                        echo "## Dependency Vulnerabilities:" >> reports/security-summary.txt
                        echo "Total: $(grep -o '"severity"' reports/snyk-deps-report.json | wc -l)" >> reports/security-summary.txt
                        echo "Critical: $(grep -o '"severity":"critical"' reports/snyk-deps-report.json | wc -l)" >> reports/security-summary.txt
                        echo "High: $(grep -o '"severity":"high"' reports/snyk-deps-report.json | wc -l)" >> reports/security-summary.txt
                        echo "Medium: $(grep -o '"severity":"medium"' reports/snyk-deps-report.json | wc -l)" >> reports/security-summary.txt
                        echo "Low: $(grep -o '"severity":"low"' reports/snyk-deps-report.json | wc -l)" >> reports/security-summary.txt
                        echo "" >> reports/security-summary.txt
                    fi

                    if [ -f reports/snyk-container-report.json ]; then
                        echo "## Container Vulnerabilities:" >> reports/security-summary.txt
                        echo "Total: $(grep -o '"severity"' reports/snyk-container-report.json | wc -l)" >> reports/security-summary.txt
                        echo "" >> reports/security-summary.txt
                    fi

                    if [ -f reports/snyk-code-report.json ]; then
                        echo "## Code Issues:" >> reports/security-summary.txt
                        echo "Total: $(grep -o '"issue"' reports/snyk-code-report.json | wc -l)" >> reports/security-summary.txt
                        echo "" >> reports/security-summary.txt
                    fi

                    cat reports/security-summary.txt
                '''
            }
        }

        stage('Archive Reports') {
            steps {
                archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true

                script {
                    if (fileExists('reports/security-summary.txt')) {
                        echo "Security reports have been archived"
                    }
                }
            }
        }

        stage('Snyk Monitor - Push to Dashboard') {
            steps {
                sh '''
                    echo "Pushing results to Snyk dashboard for continuous monitoring..."

                    ${SNYK_PATH} monitor --file=./requirements.txt \
                        --project-name="vulnerable-python-app-deps-build-${BUILD_NUMBER}" \
                        --remote-repo-url="https://github.com/Ray19823/vulnerable-python-app" || true

                    ${SNYK_PATH} container monitor ${DOCKER_IMAGE}:${DOCKER_TAG} \
                        --project-name="vulnerable-python-app-container-build-${BUILD_NUMBER}" || true

                    ${SNYK_PATH} code test --report \
                        --project-name="vulnerable-python-app-code-build-${BUILD_NUMBER}" || true

                    echo "Projects should now appear in Snyk dashboard."
                '''
            }
        }
    }

    post {
        always {
            sh '''
                echo "Cleaning up Docker images..."
                docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} || true
            '''
        }

        success {
            echo 'Pipeline completed successfully!'
        }

        unstable {
            echo 'Pipeline completed with warnings. Security vulnerabilities detected!'
            echo 'Review the security reports in the archived artifacts.'
        }

        failure {
            echo 'Pipeline failed. Check the logs for details.'
        }
    }
}
