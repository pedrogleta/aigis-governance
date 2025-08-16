module.exports = {
  apps: [
    {
      name: 'setup-frontend',
      script: 'setup-frontend.sh',
      cwd: './frontend',
      autorestart: false,
    },
    {
      name: 'setup-backend',
      script: 'setup-backend.sh',
      cwd: './backend',
      autorestart: false,
    },
    {
      name: 'setup-agent-gateway',
      script: 'setup-agent-gateway.sh',
      cwd: './agent-gateway',
      autorestart: false,
    },
    {
      name: 'minio',
      script: 'setup-minio.sh',
      cwd: './docker/minio',
      autorestart: false,
    },
  ],
};
