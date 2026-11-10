USE appointmed;

CREATE TABLE IF NOT EXISTS site_content (
    content_key   VARCHAR(50) PRIMARY KEY,
    content_value MEDIUMTEXT NOT NULL,
    updated_by    INT NULL,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_site_content_updated_by FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB;