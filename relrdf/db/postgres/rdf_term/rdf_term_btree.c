
#include "rdf_term.h"

#include "btree_gist.h"
#include "btree_utils_var.h"
#include "utils/builtins.h"

/* == Declarations == */

PG_FUNCTION_INFO_V1(gbt_term_compress);
PG_FUNCTION_INFO_V1(gbt_term_union);
PG_FUNCTION_INFO_V1(gbt_term_picksplit);
PG_FUNCTION_INFO_V1(gbt_term_consistent);
PG_FUNCTION_INFO_V1(gbt_term_penalty);
PG_FUNCTION_INFO_V1(gbt_term_same);

Datum		gbt_term_compress(PG_FUNCTION_ARGS);
Datum		gbt_term_union(PG_FUNCTION_ARGS);
Datum		gbt_term_picksplit(PG_FUNCTION_ARGS);
Datum		gbt_term_consistent(PG_FUNCTION_ARGS);
Datum		gbt_term_penalty(PG_FUNCTION_ARGS);
Datum		gbt_term_same(PG_FUNCTION_ARGS);

/* define for comparison */

static bool
gbt_termgt(const void *a, const void *b)
{
	return compare_terms((RdfTerm *)a, (RdfTerm *)b) > 0;
}

static bool
gbt_termge(const void *a, const void *b)
{
	return compare_terms((RdfTerm *)a, (RdfTerm *)b) >= 0;
}

static bool
gbt_termeq(const void *a, const void *b)
{
	return compare_terms((RdfTerm *)a, (RdfTerm *)b) == 0;
}

static bool
gbt_termle(const void *a, const void *b)
{
	return compare_terms((RdfTerm *)a, (RdfTerm *)b) <= 0;
}

static bool
gbt_termlt(const void *a, const void *b)
{
	return compare_terms((RdfTerm *)a, (RdfTerm *)b) < 0;
}

static int32
gbt_termcmp(const bytea *a, const bytea *b)
{
	return compare_terms((RdfTerm *)a, (RdfTerm *)b);
}

static gbtree_vinfo tinfo =
{
	gbt_t_term,
	0,
	FALSE,
	gbt_termgt,
	gbt_termge,
	gbt_termeq,
	gbt_termle,
	gbt_termlt,
	gbt_termcmp,
	NULL
};


/**************************************************
 * term ops
 **************************************************/

Datum
gbt_term_compress(PG_FUNCTION_ARGS)
{
	GISTENTRY  *entry = (GISTENTRY *) PG_GETARG_POINTER(0);

	if (tinfo.eml == 0)
	{
		tinfo.eml = pg_database_encoding_max_length();
	}

	PG_RETURN_POINTER(gbt_var_compress(entry, &tinfo));
}

Datum
gbt_term_consistent(PG_FUNCTION_ARGS)
{
	GISTENTRY  *entry = (GISTENTRY *) PG_GETARG_POINTER(0);
	GBT_VARKEY *key = (GBT_VARKEY *) DatumGetPointer(entry->key);
	void	   *query = (void *) PG_GETARG_RDF_TERM(1);
	StrategyNumber strategy = (StrategyNumber) PG_GETARG_UINT16(2);
	bool		retval = FALSE;
	GBT_VARKEY_R r = gbt_var_key_readable(key);

	if (tinfo.eml == 0)
	{
		tinfo.eml = pg_database_encoding_max_length();
	}

	retval = gbt_var_consistent(&r, query, &strategy, GIST_LEAF(entry), &tinfo);

	PG_RETURN_BOOL(retval);
}

Datum
gbt_term_union(PG_FUNCTION_ARGS)
{
	GistEntryVector *entryvec = (GistEntryVector *) PG_GETARG_POINTER(0);
	int32	   *size = (int *) PG_GETARG_POINTER(1);

	PG_RETURN_POINTER(gbt_var_union(entryvec, size, &tinfo));
}


Datum
gbt_term_picksplit(PG_FUNCTION_ARGS)
{
	GistEntryVector *entryvec = (GistEntryVector *) PG_GETARG_POINTER(0);
	GIST_SPLITVEC *v = (GIST_SPLITVEC *) PG_GETARG_POINTER(1);

	gbt_var_picksplit(entryvec, v, &tinfo);
	PG_RETURN_POINTER(v);
}

Datum
gbt_term_same(PG_FUNCTION_ARGS)
{
	Datum		d1 = PG_GETARG_DATUM(0);
	Datum		d2 = PG_GETARG_DATUM(1);
	bool	   *result = (bool *) PG_GETARG_POINTER(2);

	PG_RETURN_POINTER(gbt_var_same(result, d1, d2, &tinfo));
}


Datum
gbt_term_penalty(PG_FUNCTION_ARGS)
{
	GISTENTRY  *o = (GISTENTRY *) PG_GETARG_POINTER(0);
	GISTENTRY  *n = (GISTENTRY *) PG_GETARG_POINTER(1);
	float	   *result = (float *) PG_GETARG_POINTER(2);

	PG_RETURN_POINTER(gbt_var_penalty(result, o, n, &tinfo));
}
