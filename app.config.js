module.exports = {
  apps: [
    {
      name: 'agent-gateway',
      script: 'start-agent-gateway.sh',
      cwd: './agent-gateway',
    },
    {
      name: 'frontend',
      script: 'start-frontend.sh',
      cwd: './frontend',
    },
    {
      name: 'backend',
      script: 'start-backend.sh',
      cwd: './backend',
    },
  ],
};
