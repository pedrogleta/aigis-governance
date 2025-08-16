// MinIO service that communicates with the Express.js microservice
const MINIO_SERVICE_URL = 'http://localhost:3001';

export class MinioService {
  // Get the count of files in the bucket
  static async getFileCount(): Promise<number> {
    try {
      const response = await fetch(`${MINIO_SERVICE_URL}/files/count`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.count;
    } catch (error) {
      console.error('Error getting file count from MinIO service:', error);
      return 0;
    }
  }

  // Get the latest file added to the bucket
  static async getLatestFile(): Promise<string | null> {
    try {
      const response = await fetch(`${MINIO_SERVICE_URL}/files/latest`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.filename;
    } catch (error) {
      console.error('Error getting latest file from MinIO service:', error);
      return null;
    }
  }

  // Get a presigned URL for a file
  static async getFileUrl(filename: string): Promise<string> {
    try {
      const response = await fetch(
        `${MINIO_SERVICE_URL}/files/${encodeURIComponent(filename)}/url`,
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.url;
    } catch (error) {
      console.error('Error getting presigned URL for file:', filename, error);
      throw error;
    }
  }

  // Check if bucket exists, create if not
  static async ensureBucket(): Promise<void> {
    try {
      // The Express.js service handles bucket creation automatically
      const response = await fetch(`${MINIO_SERVICE_URL}/health`);
      if (!response.ok) {
        throw new Error(`MinIO service is not healthy: ${response.status}`);
      }
      console.log('MinIO service is healthy');
    } catch (error) {
      console.error('Error ensuring bucket exists:', error);
      throw error;
    }
  }

  // List all files in the bucket
  static async listFiles(): Promise<
    Array<{ name: string; size: number; lastModified: Date }>
  > {
    try {
      const response = await fetch(`${MINIO_SERVICE_URL}/files`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.files.map((file: any) => ({
        name: file.name,
        size: file.size,
        lastModified: new Date(file.lastModified),
      }));
    } catch (error) {
      console.error('Error listing files from MinIO service:', error);
      return [];
    }
  }
}
