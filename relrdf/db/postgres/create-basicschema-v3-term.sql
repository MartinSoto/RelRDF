
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

CREATE INDEX statements_object_hash_index
  ON statements USING hash (object);
  
DROP TABLE IF EXISTS types;

CREATE TABLE types (
  id int PRIMARY KEY,
  type_uri varchar(255),
  lang_tag varchar(255)
);

CREATE UNIQUE INDEX types_type_uri_index
  ON types (type_uri);
CREATE UNIQUE INDEX types_lang_tag_index
  ON types (lang_tag);

INSERT INTO types VALUES

  (2, 'http://www.w3.org/2001/XMLSchema#string', NULL),

  (1*4096+0, 'http://www.w3.org/2001/XMLSchema#integer', NULL),
  (1*4096+1, 'http://www.w3.org/2001/XMLSchema#decimal', NULL),
  (1*4096+2, 'http://www.w3.org/2001/XMLSchema#float', NULL),
  (1*4096+3, 'http://www.w3.org/2001/XMLSchema#double', NULL),
  (1*4096+4, 'http://www.w3.org/2001/XMLSchema#positiveInteger', NULL),
  (1*4096+5, 'http://www.w3.org/2001/XMLSchema#negativeInteger', NULL),
  (1*4096+6, 'http://www.w3.org/2001/XMLSchema#nonPositiveInteger', NULL),
  (1*4096+7, 'http://www.w3.org/2001/XMLSchema#nonNegativeInteger', NULL),
  (1*4096+8, 'http://www.w3.org/2001/XMLSchema#long', NULL),
  (1*4096+9, 'http://www.w3.org/2001/XMLSchema#int', NULL),
  (1*4096+10, 'http://www.w3.org/2001/XMLSchema#short', NULL),
  (1*4096+11, 'http://www.w3.org/2001/XMLSchema#byte', NULL),
  (1*4096+12, 'http://www.w3.org/2001/XMLSchema#unsignedLong', NULL),
  (1*4096+13, 'http://www.w3.org/2001/XMLSchema#unsignedInt', NULL),
  (1*4096+14, 'http://www.w3.org/2001/XMLSchema#unsignedShort', NULL),
  (1*4096+15, 'http://www.w3.org/2001/XMLSchema#unsignedByte', NULL),

  (2*4096+0, 'http://www.w3.org/2001/XMLSchema#boolean', NULL),

  (3*4096+0, 'http://www.w3.org/2001/XMLSchema#dateTime', NULL),
  (3*4096+256, 'http://www.w3.org/2001/XMLSchema#date', NULL),
  (3*4096+2*256, 'http://www.w3.org/2001/XMLSchema#time', NULL);

DROP SEQUENCE IF EXISTS data_types_id_seq;
CREATE SEQUENCE data_types_id_seq
  INCREMENT BY 256
  START WITH 17152
  NO CYCLE;

DROP SEQUENCE IF EXISTS language_tags_id_seq;
CREATE SEQUENCE language_tags_id_seq
  INCREMENT BY 1
  START WITH 3
  NO CYCLE;

DROP TABLE IF EXISTS graphs;
CREATE TABLE graphs (
  graph_id serial PRIMARY KEY,
  graph_uri text NOT NULL,
  timeout timestamp
);

CREATE UNIQUE INDEX graph_uri_index ON graphs (graph_uri);

DROP TABLE IF EXISTS graph_statement;
CREATE TABLE graph_statement (
  graph_id integer NOT NULL,
  stmt_id integer NOT NULL,
  PRIMARY KEY (graph_id, stmt_id)
);

CREATE INDEX graph_statement_stmt_id_index ON graph_statement (stmt_id);

DROP TABLE IF EXISTS prefixes;
CREATE TABLE prefixes (
  prefix varchar(31) NOT NULL PRIMARY KEY,
  namespace varchar(255) NOT NULL
);

INSERT INTO prefixes (prefix, namespace) VALUES 
  ('vmxt', 'http://www.v-modell-xt.de/schema/1#'),
  ('vmxti', 'http://www.v-modell-xt.de/model/1#'),
  ('vmxtg', 'http://www.v-modell-xt.de/graphs/1#');
  
  
GRANT ALL ON 
  types, data_types_id_seq, language_tags_id_seq, 
  prefixes, relrdf_schema_version,
  statements, statements_id_seq, 
  graphs, graphs_graph_id_seq, graph_statement TO vmodell;

/* Stored procedures handling type lookups */

CREATE LANGUAGE 'plpgsql';

-- Looks up or creates type entry for given type URI / language tag
CREATE OR REPLACE FUNCTION rdf_term_literal_type_to_id(uri text, tag text) RETURNS int4 AS $$
  DECLARE
    type_id int4;
  BEGIN
    SELECT INTO type_id id FROM types WHERE type_uri = uri OR lang_tag = tag;
    IF NOT FOUND THEN
      IF uri IS NOT NULL THEN
        type_id := nextval('data_types_id_seq');
      ELSE
        type_id := nextval('language_tags_id_seq');
      END IF;
      INSERT INTO types VALUES (type_id, uri, tag);
    END IF;
    RETURN type_id;
  END
$$ LANGUAGE 'plpgsql' VOLATILE;

-- Creates a literal with given type and data
CREATE OR REPLACE FUNCTION rdf_term_literal(val text, type_uri text, lang_tag text) RETURNS rdf_term AS $$
  DECLARE
    type_id int4;
  BEGIN
    IF type_uri IS NULL AND lang_tag IS NULL THEN
      type_id = 1;
    ELSE
      type_id = rdf_term_literal_type_to_id(type_uri, lang_tag);
    END IF;
    RETURN rdf_term(type_id, val);
  END
$$ LANGUAGE 'plpgsql' VOLATILE;

-- Creates a resource object with given data
CREATE OR REPLACE FUNCTION rdf_term_resource(uri text) RETURNS rdf_term AS $$
  SELECT rdf_term(0, $1);
$$ LANGUAGE SQL IMMUTABLE STRICT;

-- Creates a resource or a literal (used by model import)
CREATE OR REPLACE FUNCTION rdf_term_create(val text, is_res int, type_uri text, lang_tag text) RETURNS rdf_term AS $$
  SELECT CASE WHEN $2 <> 0 THEN rdf_term_resource($1) ELSE rdf_term_literal($1, $3, $4) END;
$$ LANGUAGE SQL VOLATILE;


-- Looks up the language tag for a given type id (returns an empty literal if it doesn't exist)
CREATE OR REPLACE FUNCTION rdf_term_lang_tag_by_id(type_id int4) RETURNS rdf_term AS $$
  BEGIN
    RETURN rdf_term(1, COALESCE((SELECT lang_tag FROM types WHERE id = type_id), ''));
  END
$$ LANGUAGE 'plpgsql' IMMUTABLE STRICT;

-- Looks up the data type URI for a given term (returns empty URI if id doesn't exist)
CREATE OR REPLACE FUNCTION rdf_term_type_uri_by_id(type_id int4) RETURNS rdf_term AS $$
  BEGIN
    RETURN rdf_term(0, COALESCE((SELECT type_uri FROM types WHERE id = type_id), ''));
  END
$$ LANGUAGE 'plpgsql' IMMUTABLE STRICT;


-- Returns the ID for a language tag given as simple literal.
-- Gives -1 for an empty literal and -2 for an unknown language tag (so they are unequal to both)
CREATE OR REPLACE FUNCTION rdf_term_lang_tag_to_id(tag rdf_term) RETURNS int4 AS $$
  BEGIN
    -- Type check
    IF rdf_term_get_type_id(tag) <> 1 THEN RETURN NULL; END IF;
    -- Empty?
    IF text(rdf_term_to_string(tag)) = '' THEN RETURN -1; END IF;
    -- Lookup type id
    RETURN COALESCE((SELECT id FROM types WHERE lang_tag = text(rdf_term_to_string(tag))), -2);
  END
$$ LANGUAGE 'plpgsql' IMMUTABLE STRICT;

-- Returns the ID for a data type IRI.
-- Gives -1 for an empty IRI and -2 for an unknown data type IRI (so they are unequal to both)
CREATE OR REPLACE FUNCTION rdf_term_type_uri_to_id(uri rdf_term) RETURNS int4 AS $$
  BEGIN
    -- Type check
    IF rdf_term_get_type_id(uri) <> 0 THEN RETURN NULL; END IF;
    -- Empty?
    IF text(rdf_term_to_string(uri)) = '' THEN RETURN -1; END IF;
    -- Lookup type id
    RETURN COALESCE((SELECT id FROM types WHERE type_uri = text(rdf_term_to_string(uri))), -2);
  END
$$ LANGUAGE 'plpgsql' IMMUTABLE STRICT;


-- Returns type id only if it's a valid language type id
-- Gives NULL if it's actually a resource and -1 otherwise.
CREATE OR REPLACE FUNCTION rdf_term_get_lang_type_id(term rdf_term) RETURNS int4 AS $$
  DECLARE
    type_id int4;
  BEGIN
    type_id := rdf_term_get_type_id(term);
    RETURN (CASE 
      WHEN type_id = 0 THEN NULL
      WHEN type_id >= 3 AND type_id < 4096 THEN type_id
      ELSE -1 END);
  END
$$ LANGUAGE 'plpgsql' IMMUTABLE STRICT;

-- Returns type id only if it's a valid data type id (-1 otherwise)
CREATE OR REPLACE FUNCTION rdf_term_get_data_type_id(term rdf_term) RETURNS int4 AS $$
  DECLARE
    type_id int4;
  BEGIN
    type_id := rdf_term_get_type_id(term);
    RETURN (CASE 
      WHEN type_id = 1 THEN 2 -- simple literals actually have a data type uri of xsd:string
      WHEN type_id = 2 THEN 2
      WHEN type_id >= 4096 THEN type_id
      ELSE NULL END);
  END
$$ LANGUAGE 'plpgsql' IMMUTABLE STRICT;

