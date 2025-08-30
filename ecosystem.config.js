module.exports = {
  apps: [
    {
      name: 'chromadb-server',
      script: 'chroma',
      args: 'run --path ./chroma_db --host 0.0.0.0 --port 8004',
      cwd: '/root/Miners',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/root/Miners/logs/chromadb-error.log',
      out_file: '/root/Miners/logs/chromadb-out.log',
      log_file: '/root/Miners/logs/chromadb-combined.log',
      time: true
    },
    {
      name: 'miners-main',
      script: 'python3',
      args: 'main.py run_all',
      cwd: '/root/Miners',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      restart_delay: 5000,
      max_restarts: 10,
      min_uptime: '10s',
      env: {
        PYTHONPATH: '/root/Miners',
        PYTHONUNBUFFERED: '1'
      },
      error_file: '/root/Miners/logs/miners-error.log',
      out_file: '/root/Miners/logs/miners-out.log',
      log_file: '/root/Miners/logs/miners-combined.log',
      time: true
    }
  ]
};
