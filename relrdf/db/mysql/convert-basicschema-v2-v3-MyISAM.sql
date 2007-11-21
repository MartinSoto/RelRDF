DROP TABLE IF EXISTS relrdf_schema_version;

CREATE TABLE relrdf_schema_version (
  name varchar(255),
  version integer
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO relrdf_schema_version (name, version)
  VALUES ('basic', 3);


DROP TABLE IF EXISTS twoway;

CREATE TABLE twoway (
  version_a integer unsigned NOT NULL
	 COMMENT 'Version identifier of the first compared version',
  version_b integer unsigned NOT NULL
	 COMMENT 'Version identifier of the second compared version',
  stmt_id integer unsigned NOT NULL
	 COMMENT 'A statement identifier',
  context char(2) NOT NULL
	 COMMENT 'Comparison context',
  UNIQUE KEY (version_a, version_b, stmt_id),
  KEY (stmt_id),
  KEY (context)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS twoway_use_time;

CREATE TABLE twoway_use_time (
  version_a integer unsigned NOT NULL
	 COMMENT 'Version identifier of the first compared version',
  version_b integer unsigned NOT NULL
	 COMMENT 'Version identifier of the second compared version',
  time datetime NOT NULL
	 COMMENT 'Time at which this comparison was last used',
  UNIQUE KEY (version_a, version_b)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS twoway_conns;

CREATE TABLE twoway_conns (
  version_a integer unsigned NOT NULL
	 COMMENT 'Version identifier of the first compared version',
  version_b integer unsigned NOT NULL
	 COMMENT 'Version identifier of the second compared version',
  connection integer unsigned NOT NULL
	 COMMENT 'Identifier of the connection using this comparison'
) ENGINE=MyISAM DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS threeway;

CREATE TABLE threeway (
  version_a integer unsigned NOT NULL
	 COMMENT 'Version identifier of the first compared version',
  version_b integer unsigned NOT NULL
	 COMMENT 'Version identifier of the second compared version',
  version_c integer unsigned NOT NULL
	 COMMENT 'Version identifier of the third compared version',
  stmt_id integer unsigned NOT NULL
	 COMMENT 'A statement identifier',
  context char(3) NOT NULL
	 COMMENT 'Comparison context',
  UNIQUE KEY (version_a, version_b, version_c, stmt_id),
  KEY (stmt_id),
  KEY (context)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS threeway_use_time;

CREATE TABLE threeway_use_time (
  version_a integer unsigned NOT NULL
	 COMMENT 'Version identifier of the first compared version',
  version_b integer unsigned NOT NULL
	 COMMENT 'Version identifier of the second compared version',
  version_c integer unsigned NOT NULL
	 COMMENT 'Version identifier of the third compared version',
  time datetime NOT NULL
	 COMMENT 'Time at which this comparison was last used',
  UNIQUE KEY (version_a, version_b, version_c)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS threeway_conns;

CREATE TABLE threeway_conns (
  version_a integer unsigned NOT NULL
	 COMMENT 'Version identifier of the first compared version',
  version_b integer unsigned NOT NULL
	 COMMENT 'Version identifier of the second compared version',
  version_c integer unsigned NOT NULL
	 COMMENT 'Version identifier of the third compared version',
  connection integer unsigned NOT NULL
	 COMMENT 'Identifier of the connection using this comparison'
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
