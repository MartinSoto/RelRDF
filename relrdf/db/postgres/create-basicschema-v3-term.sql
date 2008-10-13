
DROP TABLE IF EXISTS relrdf_schema_version;

CREATE TABLE relrdf_schema_version (
  name varchar(255),
  version integer
);

INSERT INTO relrdf_schema_version (name, version)
  VALUES ('basic', 3);

DROP TABLE IF EXISTS statements;

CREATE TABLE statements (
  id SERIAL PRIMARY KEY,
  subject rdf_term NOT NULL,
  predicate rdf_term NOT NULL,
  object rdf_term NOT NULL
);

CREATE INDEX statements_predicate_index
  ON statements (predicate);  
CREATE INDEX statements_subject_predicate_index
  ON statements (subject, predicate);

CREATE INDEX statements_subject_hash_index
  ON statements USING hash (subject);
CREATE INDEX statements_predicate_hash_index
  ON statements USING hash (predicate);
CREATE INDEX statements_object_hash_index
  ON statements USING hash (object);
  
DROP TABLE IF EXISTS data_types;

CREATE TABLE data_types (
  id SERIAL PRIMARY KEY,
  uri varchar(255) NOT NULL
);

CREATE UNIQUE INDEX data_types_unique
  ON data_types (uri);

DROP TABLE IF EXISTS language_tags;

INSERT INTO data_types (id, uri) VALUES

  (1*4096+0, 'http://www.w3.org/2001/XMLSchema#integer'),
  (1*4096+1, 'http://www.w3.org/2001/XMLSchema#decimal'),
  (1*4096+2, 'http://www.w3.org/2001/XMLSchema#float'),
  (1*4096+3, 'http://www.w3.org/2001/XMLSchema#double'),
  (1*4096+4, 'http://www.w3.org/2001/XMLSchema#positiveInteger'),
  (1*4096+5, 'http://www.w3.org/2001/XMLSchema#negativeInteger'),
  (1*4096+6, 'http://www.w3.org/2001/XMLSchema#nonPositiveInteger'),
  (1*4096+7, 'http://www.w3.org/2001/XMLSchema#nonNegativeInteger'),
  (1*4096+8, 'http://www.w3.org/2001/XMLSchema#long'),
  (1*4096+9, 'http://www.w3.org/2001/XMLSchema#int'),
  (1*4096+10, 'http://www.w3.org/2001/XMLSchema#short'),
  (1*4096+11, 'http://www.w3.org/2001/XMLSchema#byte'),
  (1*4096+12, 'http://www.w3.org/2001/XMLSchema#unsignedLong'),
  (1*4096+13, 'http://www.w3.org/2001/XMLSchema#unsignedInt'),
  (1*4096+14, 'http://www.w3.org/2001/XMLSchema#unsignedShort'),
  (1*4096+15, 'http://www.w3.org/2001/XMLSchema#unsignedByte'),

  (2*4096+0, 'http://www.w3.org/2001/XMLSchema#boolean'),

  (3*4096+0, 'http://www.w3.org/2001/XMLSchema#dateTime'),
  (3*4096+1, 'http://www.w3.org/2001/XMLSchema#date'),
  (3*4096+2, 'http://www.w3.org/2001/XMLSchema#time'),

  (4*4096+0, 'http://www.w3.org/2001/XMLSchema#string');

ALTER SEQUENCE data_types_id_seq
  INCREMENT BY 256
  START WITH 17152
  NO CYCLE;
  
CREATE TABLE language_tags (
  id SERIAL PRIMARY KEY,
  tag varchar(255) NOT NULL
);

CREATE UNIQUE INDEX language_tags_unique
  ON language_tags (tag);
  
ALTER SEQUENCE language_tags_id_seq
  INCREMENT BY 1
  START WITH 2
  NO CYCLE;
  
DROP TABLE IF EXISTS version_statement;

CREATE TABLE version_statement (
  version_id integer NOT NULL,
  stmt_id integer NOT NULL,
  PRIMARY KEY (version_id, stmt_id)
);

CREATE INDEX version_statement_stmt_id_index
  ON version_statement (stmt_id);
  
DROP TABLE IF EXISTS twoway;

CREATE TABLE twoway (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  stmt_id integer NOT NULL,
  context char(2) NOT NULL,
  PRIMARY KEY (version_a, version_b, stmt_id)
);


DROP TABLE IF EXISTS twoway_use_time;

CREATE TABLE twoway_use_time (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  time timestamp NOT NULL,
  PRIMARY KEY (version_a, version_b)
);


DROP TABLE IF EXISTS twoway_conns;

CREATE TABLE twoway_conns (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  connection integer NOT NULL
);


DROP TABLE IF EXISTS threeway;

CREATE TABLE threeway (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  version_c integer NOT NULL,
  stmt_id integer NOT NULL,
  context char(3) NOT NULL,
  PRIMARY KEY (version_a, version_b, version_c, stmt_id)
);


DROP TABLE IF EXISTS threeway_use_time;

CREATE TABLE threeway_use_time (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  version_c integer NOT NULL,
  time timestamp NOT NULL,
  PRIMARY KEY (version_a, version_b, version_c)
);


DROP TABLE IF EXISTS threeway_conns;

CREATE TABLE threeway_conns (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  version_c integer NOT NULL,
  connection integer NOT NULL
);

DROP TABLE IF EXISTS prefixes;

CREATE TABLE prefixes (
  prefix varchar(31) NOT NULL PRIMARY KEY,
  namespace varchar(255) NOT NULL
);

INSERT INTO prefixes (prefix, namespace)
  VALUES ('vmxt', 'http://www.v-modell-xt.de/schema/1#'), ('vmxti', 'http://www.v-modell-xt.de/model/1#');
  
GRANT ALL ON data_types, data_types_id_seq, language_tags, language_tags_id_seq, prefixes, relrdf_schema_version, statements, statements_id_seq, twoway, twoway_conns, twoway_use_time, threeway, threeway_conns, threeway_use_time, version_statement TO vmodell;

/* Stored utility procedures */

CREATE OR REPLACE FUNCTION format_rdf_term(t rdf_term) RETURNS text AS $$
  SELECT '(' || rdf_term_to_string($1) || ',' || d.uri || ')'
   FROM data_types d WHERE d.id = rdf_term_get_type_id($1);
$$ LANGUAGE SQL STABLE STRICT;

CREATE LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION rdf_term_type_uri_to_id(type_uri text) RETURNS int4 AS $$
  DECLARE
    type_id int4;
  BEGIN
    SELECT INTO type_id id FROM data_types WHERE uri = type_uri;
    IF NOT FOUND THEN
      type_id := nextval('data_types_id_seq');
      INSERT INTO data_types (id, uri) VALUES (type_id, type_uri);
    END IF;
    RETURN type_id;
  END
$$ LANGUAGE 'plpgsql' VOLATILE STRICT;

CREATE OR REPLACE FUNCTION rdf_term_language_tag_to_id(lang_tag text) RETURNS int4 AS $$
  DECLARE
    type_id int4;
  BEGIN
    SELECT INTO type_id id FROM language_tags WHERE tag = lang_tag;
    IF NOT FOUND THEN
      type_id := nextval('language_tags_id_seq');
      INSERT INTO language_tags (id, tag) VALUES (type_id, lang_tag);
    END IF;
    RETURN type_id;
  END
$$ LANGUAGE 'plpgsql' VOLATILE STRICT;

CREATE OR REPLACE FUNCTION rdf_term_create(val text, is_res int, type_uri text, lang_tag text) RETURNS rdf_term AS $$
  DECLARE
    type_id int4;
  BEGIN
    IF is_res != 0 THEN
      type_id = 0
    ELSIF type_uri <> '' THEN
      type_id = rdf_term_type_uri_to_id(type_uri);
    ELSIF lang_tag <> '' THEN   
      type_id = rdf_term_language_tag_to_id(lang_tag);
    ELSE
      type_id = 1
    END IF;
    RETURN rdf_term(type_id, val);
  END
$$ LANGUAGE 'plpgsql' VOLATILE STRICT;

