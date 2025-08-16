module.exports = {
  apps: [
    {
      name: 'minio',
      script: 'setup-minio.sh',
      cwd: './docker/minio',
      autorestart: false,
    },
  ],
};
