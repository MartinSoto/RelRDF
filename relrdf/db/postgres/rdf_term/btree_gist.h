#ifndef __BTREE_GIST_H__
#define __BTREE_GIST_H__

#include "postgres.h"
#include "access/gist.h"
#include "access/itup.h"
#include "access/nbtree.h"

/* indexed types */

enum gbtree_type
{
	gbt_t_term,
};

/*
 * Generic btree functions
 */

Datum		gbtreekey_in(PG_FUNCTION_ARGS);

Datum		gbtreekey_out(PG_FUNCTION_ARGS);

#endif
