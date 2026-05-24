CREATE TABLE IF NOT EXISTS grader_statistics (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    oauth_consumer_key VARCHAR(255),
    lis_result_sourcedid TEXT NOT NULL,
    lis_outcome_service_url TEXT NOT NULL,
    is_correct BOOLEAN,
    attempt_type VARCHAR(16) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_grader_statistics_user_id ON grader_statistics (user_id);
CREATE INDEX IF NOT EXISTS idx_grader_statistics_created_at ON grader_statistics (created_at);
