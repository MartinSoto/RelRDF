
LOAD 'rdf_term';

DROP TYPE IF EXISTS rdf_term CASCADE;
CREATE TYPE rdf_term;

CREATE FUNCTION rdf_term_in(cstring)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
   
CREATE FUNCTION rdf_term_out(rdf_term)
  RETURNS cstring
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_recv(internal)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_send(rdf_term)
  RETURNS bytea
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE TYPE rdf_term (
  internallength = VARIABLE,
  input = rdf_term_in,
  output = rdf_term_out,
  receive = rdf_term_recv,
  send = rdf_term_send,
  alignment = int4,
  storage = extended
);


CREATE FUNCTION rdf_term(int, text)
  RETURNS rdf_term
  AS 'rdf_term', 'rdf_term_create'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_cast(int, rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_get_type_id(rdf_term)
  RETURNS int4
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_get_data_type_id(rdf_term)
  RETURNS int4
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_get_language_id(rdf_term)
  RETURNS int4
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_to_string(rdf_term)
  RETURNS cstring
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

/* Comparisons */  

CREATE FUNCTION rdf_term_types_check_compatible(rdf_term, rdf_term)
  RETURNS bool
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_types_check_incompatible(rdf_term, rdf_term)
  RETURNS bool
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_compare(rdf_term, rdf_term)
  RETURNS int4
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_less(rdf_term, rdf_term)
  RETURNS bool
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_less_equal(rdf_term, rdf_term)
  RETURNS bool
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_equal(rdf_term, rdf_term)
  RETURNS bool
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_different(rdf_term, rdf_term)
  RETURNS bool
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
   
CREATE FUNCTION rdf_term_greater_equal(rdf_term, rdf_term)
  RETURNS bool
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_greater(rdf_term, rdf_term)
  RETURNS bool
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE OPERATOR < (
	procedure = rdf_term_less,
	leftarg = rdf_term,
	rightarg = rdf_term,
	commutator = >,
	negator = >=,
	restrict = scalarltsel,
	join = scalarltjoinsel
);

CREATE OPERATOR <= (
	procedure = rdf_term_less_equal,
	leftarg = rdf_term,
	rightarg = rdf_term,
	commutator = >=,
	negator = >,
	restrict = scalarltsel,
	join = scalarltjoinsel
);

CREATE OPERATOR > (
	procedure = rdf_term_greater,
	leftarg = rdf_term,
	rightarg = rdf_term,
	commutator = <,
	negator = <=,
	restrict = scalargtsel,
	join = scalargtjoinsel
);

CREATE OPERATOR >= (
	procedure = rdf_term_greater_equal,
	leftarg = rdf_term,
	rightarg = rdf_term,
	commutator = <=,
	negator = <,
	restrict = scalargtsel,
	join = scalargtjoinsel
);

CREATE OPERATOR != (
	procedure = rdf_term_different,
	leftarg = rdf_term,
	rightarg = rdf_term,
	commutator = !=,
	negator = =,
	restrict = neqsel,
	join = neqjoinsel
);

CREATE OPERATOR = (
	procedure = rdf_term_equal,
	leftarg = rdf_term,
	rightarg = rdf_term,
	commutator = =,
	negator = !=,
	restrict = eqsel,
	join = eqjoinsel,
	hashes, merges
);

CREATE OPERATOR !== (
	procedure = rdf_term_types_check_incompatible,
	leftarg = rdf_term,
	rightarg = rdf_term,
	commutator = !==,
	negator = ===,
	restrict = neqsel,
	join = neqjoinsel
);

CREATE OPERATOR === (
	procedure = rdf_term_types_check_compatible,
	leftarg = rdf_term,
	rightarg = rdf_term,
	commutator = ===,
	negator = !==,
	restrict = eqsel,
	join = eqjoinsel,
	merges
);


/* Boolean operations and predicates */

CREATE FUNCTION rdf_term_to_bool(rdf_term)
  RETURNS bool
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_not_raw(rdf_term)
  RETURNS bool
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_not(rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_bound(rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE;

CREATE FUNCTION rdf_term_is_uri(rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_is_bnode(rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_is_literal(rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  

CREATE OPERATOR !! (
	procedure = rdf_term_to_bool,
	rightarg = rdf_term,
	negator = !
);

CREATE OPERATOR ! (
	procedure = rdf_term_not_raw,
	rightarg = rdf_term,
	negator = !!
);	

CREATE OPERATOR ^! (
	procedure = rdf_term_not,
	rightarg = rdf_term
);

/* Hash function */
 
CREATE FUNCTION rdf_term_hash(rdf_term)
  RETURNS int4
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

/* GiST support methods */

CREATE TYPE gbtreekey_var;

CREATE OR REPLACE FUNCTION gbtreekey_var_in(cstring)
	RETURNS gbtreekey_var
	AS 'rdf_term', 'gbtreekey_in'
	LANGUAGE C IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION gbtreekey_var_out(gbtreekey_var)
	RETURNS cstring
	AS 'rdf_term', 'gbtreekey_out'
	LANGUAGE C IMMUTABLE STRICT;

CREATE TYPE gbtreekey_var (
	INTERNALLENGTH = VARIABLE,
	INPUT  = gbtreekey_var_in,
	OUTPUT = gbtreekey_var_out,
	STORAGE = EXTENDED
);

CREATE FUNCTION gbt_term_consistent(internal,rdf_term,int2)
	RETURNS bool
	AS 'rdf_term'
	LANGUAGE C IMMUTABLE;

CREATE OR REPLACE FUNCTION gbt_term_compress(internal)
	RETURNS internal
	AS 'rdf_term'
	LANGUAGE C IMMUTABLE;

CREATE OR REPLACE FUNCTION gbt_term_penalty(internal,internal,internal)
	RETURNS internal
	AS 'rdf_term'
	LANGUAGE C IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION gbt_term_picksplit(internal, internal)
	RETURNS internal
	AS 'rdf_term'
	LANGUAGE C IMMUTABLE;

CREATE OR REPLACE FUNCTION gbt_term_union(bytea, internal)
	RETURNS gbtreekey_var
	AS 'rdf_term'
	LANGUAGE C IMMUTABLE;

CREATE OR REPLACE FUNCTION gbt_term_same(internal, internal, internal)
	RETURNS internal
	AS 'rdf_term'
	LANGUAGE C IMMUTABLE;

CREATE OR REPLACE FUNCTION gbt_var_decompress(internal)
	RETURNS internal
	AS 'rdf_term'
	LANGUAGE C IMMUTABLE;

/* Index definitions */

CREATE OPERATOR CLASS rdf_term_equal
	DEFAULT FOR TYPE rdf_term USING btree AS
		OPERATOR 1 <,
		OPERATOR 2 <=,
		OPERATOR 3 =,
		OPERATOR 4 >=,
		OPERATOR 5 >,
		FUNCTION 1 rdf_term_compare(rdf_term, rdf_term);

CREATE OPERATOR CLASS rdf_term_hash
	DEFAULT FOR TYPE rdf_term USING hash AS
		OPERATOR 1 = RECHECK,
		FUNCTION 1 rdf_term_hash(rdf_term);

CREATE OPERATOR CLASS gist_term_ops
	DEFAULT FOR TYPE rdf_term USING gist AS
		OPERATOR	1	<  ,
		OPERATOR	2	<= ,
		OPERATOR	3	=  ,
		OPERATOR	4	>= ,
		OPERATOR	5	>  ,
		FUNCTION	1	gbt_term_consistent (internal, rdf_term, int2),
		FUNCTION	2	gbt_term_union (bytea, internal),
		FUNCTION	3	gbt_term_compress (internal),
		FUNCTION	4	gbt_var_decompress (internal),
		FUNCTION	5	gbt_term_penalty (internal, internal, internal),
		FUNCTION	6	gbt_term_picksplit (internal, internal),
		FUNCTION	7	gbt_term_same (internal, internal, internal),
		STORAGE	    gbtreekey_var;

/* Arithmetic operators */

CREATE FUNCTION rdf_term_mul(rdf_term, rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_div(rdf_term, rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_add(rdf_term, rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_sub(rdf_term, rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_unary_plus(rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_unary_minus(rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;


CREATE OPERATOR * (
	procedure = rdf_term_mul,
	leftarg = rdf_term,
	rightarg = rdf_term
);

CREATE OPERATOR / (
	procedure = rdf_term_div,
	leftarg = rdf_term,
	rightarg = rdf_term
);

CREATE OPERATOR + (
	procedure = rdf_term_add,
	leftarg = rdf_term,
	rightarg = rdf_term
);

CREATE OPERATOR - (
	procedure = rdf_term_sub,
	leftarg = rdf_term,
	rightarg = rdf_term
);

CREATE OPERATOR + (
	procedure = rdf_term_unary_plus,
	rightarg = rdf_term
);

CREATE OPERATOR - (
	procedure = rdf_term_unary_minus,
	rightarg = rdf_term
);

/* Misc */

CREATE FUNCTION rdf_term_lang_matches(rdf_term, rdf_term)
  RETURNS rdf_term
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

