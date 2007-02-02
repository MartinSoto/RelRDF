DROP TABLE IF EXISTS relrdf_schema_version;

CREATE TABLE relrdf_schema_version (
  name varchar(255),
  version integer
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO relrdf_schema_version (name, version)
  VALUES ('basic', 2);


ALTER TABLE statements
  DROP INDEX statements_unique,
  DROP INDEX statements_subject_index,
  DROP INDEX statements_predicate_index,
  CHANGE subject subject_text longtext,
  CHANGE predicate predicate_text longtext,
  CHANGE object object_text longtext,
  ADD subject binary(16) NOT NULL AFTER hash,
  ADD predicate binary(16) NOT NULL AFTER subject,
  ADD object binary(16) NOT NULL AFTER predicate;

UPDATE statements
  SET hash = unhex(md5(concat(subject_text, predicate_text, object_text))),
      subject = unhex(md5(subject_text)),
      predicate = unhex(md5(predicate_text)),
      object = unhex(md5(object_text));

CREATE UNIQUE INDEX statements_unique
  ON statements (hash);

CREATE INDEX statements_subject_index
  ON statements (subject);
CREATE INDEX statements_predicate_index
  ON statements (predicate);
CREATE INDEX statements_object_index
  ON statements (object);

DROP TABLE IF EXISTS not_versioned_statements;

DROP PROCEDURE IF EXISTS insert_version;

DELIMITER //

CREATE PROCEDURE insert_version(version_id INT)
BEGIN
  UPDATE statements_temp
    SET hash = unhex(md5(concat(subject_text, predicate_text, object_text)));

  INSERT INTO data_types (uri)
    SELECT s.object_type
    FROM statements_temp s
  ON DUPLICATE KEY UPDATE uri = uri;

  INSERT INTO statements (hash, subject, predicate, object,
                          subject_text, predicate_text, object_type,
                          object_text)
    SELECT s.hash, unhex(md5(subject_text)), unhex(md5(predicate_text)),
           unhex(md5(object_text)), s.subject_text, s.predicate_text,
           dt.id, s.object_text
    FROM statements_temp s, data_types dt
    WHERE s.object_type = dt.uri
  ON DUPLICATE KEY UPDATE statements.subject = statements.subject;

  INSERT INTO version_statement (version_id, stmt_id)
    SELECT version_id AS v_id, s.id
    FROM statements s, statements_temp st
    WHERE s.hash = st.hash
  ON DUPLICATE KEY UPDATE version_id = version_id;

  DROP TABLE statements_temp;
END
//

DELIMITER ;
