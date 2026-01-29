// MongoDB initialization script
// Creates database and collections for OmniSearch

// Use admin database
db = db.getSiblingDB('omnisearch');

// Create collections
db.createCollection('click_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'timestamp', 'event_type'],
      properties: {
        _id: { bsonType: 'objectId' },
        user_id: { bsonType: 'string' },
        session_id: { bsonType: 'string' },
        timestamp: { bsonType: 'date' },
        event_type: { enum: ['impression', 'click'] },
        query: { bsonType: 'string' },
        result_id: { bsonType: 'string' },
        position: { bsonType: 'int' },
        rank: { bsonType: 'int' },
        response_time_ms: { bsonType: 'double' },
        variant: { bsonType: 'string' },
        experiment_id: { bsonType: 'string' }
      }
    }
  }
});

db.createCollection('impressions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'timestamp', 'query'],
      properties: {
        _id: { bsonType: 'objectId' },
        user_id: { bsonType: 'string' },
        query: { bsonType: 'string' },
        timestamp: { bsonType: 'date' },
        variant: { bsonType: 'string' },
        response_time_ms: { bsonType: 'double' }
      }
    }
  }
});

db.createCollection('experiments', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'created_at'],
      properties: {
        _id: { bsonType: 'objectId' },
        name: { bsonType: 'string' },
        description: { bsonType: 'string' },
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' },
        status: { enum: ['active', 'completed', 'paused'] },
        variants: { bsonType: 'array' },
        traffic_allocation: { bsonType: 'object' }
      }
    }
  }
});

// Create indexes
db.click_events.createIndex({ user_id: 1, timestamp: -1 });
db.click_events.createIndex({ query: 1, timestamp: -1 });
db.click_events.createIndex({ variant: 1, timestamp: -1 });
db.click_events.createIndex({ experiment_id: 1 });
db.click_events.createIndex({ timestamp: -1 }, { expireAfterSeconds: 7776000 }); // 90 days TTL

db.impressions.createIndex({ user_id: 1, timestamp: -1 });
db.impressions.createIndex({ query: 1, timestamp: -1 });
db.impressions.createIndex({ variant: 1, timestamp: -1 });
db.impressions.createIndex({ timestamp: -1 }, { expireAfterSeconds: 7776000 }); // 90 days TTL

db.experiments.createIndex({ name: 1 }, { unique: true });
db.experiments.createIndex({ created_at: -1 });
db.experiments.createIndex({ status: 1 });

// Enable replication (required for MongoDB 4.0+)
rs.initiate({
  _id: "rs0",
  members: [
    {
      _id: 0,
      host: "mongo:27017"
    }
  ]
});

print("✓ MongoDB initialization complete");
print("✓ Database: omnisearch");
print("✓ Collections: click_events, impressions, experiments");
print("✓ Indexes created");
print("✓ Replication initiated");
