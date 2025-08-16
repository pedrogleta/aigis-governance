const express = require('express');
const cors = require('cors');
const { Client } = require('minio');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// MinIO client configuration with environment variables
const minioClient = new Client({
  endPoint: process.env.MINIO_HOST || 'localhost',
  port: 9000,
  useSSL: false,
  accessKey: process.env.MINIO_ROOT_USER || 'minioadmin',
  secretKey: process.env.MINIO_ROOT_PASSWORD || 'minioadmin',
});

const BUCKET_NAME = 'aigis-data-governance';

// Ensure bucket exists on startup
async function ensureBucket() {
  try {
    const exists = await minioClient.bucketExists(BUCKET_NAME);
    if (!exists) {
      await minioClient.makeBucket(BUCKET_NAME);
      console.log('Created MinIO bucket:', BUCKET_NAME);
    } else {
      console.log('MinIO bucket already exists:', BUCKET_NAME);
    }
  } catch (error) {
    console.error('Error ensuring bucket exists:', error);
  }
}

// Initialize bucket on startup
ensureBucket();

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'minio-service' });
});

// Get file count in bucket
app.get('/files/count', async (req, res) => {
  try {
    const objectsStream = minioClient.listObjects(BUCKET_NAME, '', true);
    let count = 0;

    return new Promise((resolve, reject) => {
      objectsStream.on('data', () => {
        count++;
      });

      objectsStream.on('end', () => {
        resolve(count);
      });

      objectsStream.on('error', (err) => {
        reject(err);
      });
    })
      .then((count) => {
        res.json({ count });
      })
      .catch((error) => {
        console.error('Error getting file count:', error);
        res.status(500).json({ error: 'Failed to get file count' });
      });
  } catch (error) {
    console.error('Error getting file count:', error);
    res.status(500).json({ error: 'Failed to get file count' });
  }
});

// Get latest file in bucket
app.get('/files/latest', async (req, res) => {
  try {
    const objectsStream = minioClient.listObjects(BUCKET_NAME, '', true);
    let latestFile = null;
    let latestTime = 0;

    return new Promise((resolve, reject) => {
      objectsStream.on('data', (obj) => {
        if (
          obj.lastModified &&
          obj.lastModified.getTime() > latestTime &&
          obj.name
        ) {
          latestTime = obj.lastModified.getTime();
          latestFile = obj.name;
        }
      });

      objectsStream.on('end', () => {
        resolve(latestFile);
      });

      objectsStream.on('error', (err) => {
        reject(err);
      });
    })
      .then((latestFile) => {
        if (latestFile) {
          res.json({ filename: latestFile, lastModified: latestTime });
        } else {
          res.json({ filename: null, lastModified: null });
        }
      })
      .catch((error) => {
        console.error('Error getting latest file:', error);
        res.status(500).json({ error: 'Failed to get latest file' });
      });
  } catch (error) {
    console.error('Error getting latest file:', error);
    res.status(500).json({ error: 'Failed to get latest file' });
  }
});

// Get presigned URL for a file
app.get('/files/:filename/url', async (req, res) => {
  try {
    const { filename } = req.params;
    const url = await minioClient.presignedGetObject(
      BUCKET_NAME,
      filename,
      24 * 60 * 60,
    ); // 24 hours expiry
    res.json({ url });
  } catch (error) {
    console.error('Error getting presigned URL for file:', filename, error);
    res.status(500).json({ error: 'Failed to get presigned URL' });
  }
});

// List all files in bucket
app.get('/files', async (req, res) => {
  try {
    const objectsStream = minioClient.listObjects(BUCKET_NAME, '', true);
    const files = [];

    return new Promise((resolve, reject) => {
      objectsStream.on('data', (obj) => {
        files.push({
          name: obj.name,
          size: obj.size,
          lastModified: obj.lastModified,
          etag: obj.etag,
        });
      });

      objectsStream.on('end', () => {
        resolve(files);
      });

      objectsStream.on('error', (err) => {
        reject(err);
      });
    })
      .then((files) => {
        res.json({ files });
      })
      .catch((error) => {
        console.error('Error listing files:', error);
        res.status(500).json({ error: 'Failed to list files' });
      });
  } catch (error) {
    console.error('Error listing files:', error);
    res.status(500).json({ error: 'Failed to list files' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`MinIO service running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(
    `Connecting to MinIO at: ${process.env.MINIO_HOST || 'localhost'}:9000`,
  );
});
