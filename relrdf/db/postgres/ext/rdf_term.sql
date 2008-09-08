
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

CREATE FUNCTION rdf_term(int, double precision)
  RETURNS rdf_term
  AS 'rdf_term', 'rdf_term_double'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term(int, text)
  RETURNS rdf_term
  AS 'rdf_term', 'rdf_term_text'
  LANGUAGE C IMMUTABLE STRICT;


CREATE FUNCTION rdf_term_get_type_id(rdf_term)
  RETURNS int4
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_is_num_type(rdf_term)
  RETURNS bool
  AS 'rdf_term', 'rdf_term_is_num_type_t'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_is_num_type(int4)
  RETURNS bool
  AS 'rdf_term', 'rdf_term_is_num_type_i'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_is_text_type(rdf_term)
  RETURNS bool
  AS 'rdf_term', 'rdf_term_is_text_type_t'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_is_text_type(int4)
  RETURNS bool
  AS 'rdf_term', 'rdf_term_is_text_type_i'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_to_string(rdf_term)
  RETURNS cstring
  AS 'rdf_term'
  LANGUAGE C IMMUTABLE STRICT;

/* Comparisons */  

CREATE FUNCTION rdf_term_types_compatible(rdf_term, rdf_term)
  RETURNS bool
  AS 'rdf_term', 'rdf_term_types_compatible_tt'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_types_incompatible(rdf_term, rdf_term)
  RETURNS bool
  AS 'rdf_term', 'rdf_term_types_incompatible_tt'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_types_compatible(int4, rdf_term)
  RETURNS bool
  AS 'rdf_term', 'rdf_term_types_compatible_it'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_types_incompatible(int4, rdf_term)
  RETURNS bool
  AS 'rdf_term', 'rdf_term_types_incompatible_it'
  LANGUAGE C IMMUTABLE STRICT;
  
CREATE FUNCTION rdf_term_types_compatible(rdf_term, int4)
  RETURNS bool
  AS 'rdf_term', 'rdf_term_types_compatible_ti'
  LANGUAGE C IMMUTABLE STRICT;

CREATE FUNCTION rdf_term_types_incompatible(rdf_term, int4)
  RETURNS bool
  AS 'rdf_term', 'rdf_term_types_incompatible_ti'
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
	procedure = rdf_term_types_incompatible,
	leftarg = rdf_term,
	rightarg = rdf_term,
	commutator = !==,
	negator = ===,
	restrict = neqsel,
	join = neqjoinsel
);

CREATE OPERATOR === (
	procedure = rdf_term_types_compatible,
	leftarg = rdf_term,
	rightarg = rdf_term,
	commutator = ===,
	negator = !==,
	restrict = eqsel,
	join = eqjoinsel,
	merges
);

CREATE OPERATOR !== (
	procedure = rdf_term_types_incompatible,
	leftarg = rdf_term,
	rightarg = int4,
	commutator = !==,
	negator = ===,
	restrict = neqsel,
	join = neqjoinsel
);

CREATE OPERATOR === (
	procedure = rdf_term_types_compatible,
	leftarg = rdf_term,
	rightarg = int4,
	commutator = ===,
	negator = !==,
	restrict = eqsel,
	join = eqjoinsel,
	merges
);

CREATE OPERATOR !== (
	procedure = rdf_term_types_incompatible,
	leftarg = int4,
	rightarg = rdf_term,
	commutator = !==,
	negator = ===,
	restrict = neqsel,
	join = neqjoinsel
);

CREATE OPERATOR === (
	procedure = rdf_term_types_compatible,
	leftarg = int4,
	rightarg = rdf_term,
	commutator = ===,
	negator = !==,
	restrict = eqsel,
	join = eqjoinsel,
	merges
);

/* Boolean operations */

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
		
CREATE OPERATOR CLASS rdf_term_compatible
	FOR TYPE rdf_term USING btree AS
		OPERATOR 1 <,
		OPERATOR 2 <=,
		OPERATOR 3 === RECHECK,
		OPERATOR 4 >=,
		OPERATOR 5 >,
		FUNCTION 1 rdf_term_compare(rdf_term, rdf_term);

