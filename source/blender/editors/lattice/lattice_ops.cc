/* SPDX-FileCopyrightText: 2008 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edlattice
 */

#include "DNA_lattice_types.h"

#include "BKE_key.hh"

#include "WM_api.hh"

#include "ED_lattice.hh"
#include "ED_screen.hh"

#include "lattice_intern.hh"

void ED_operatortypes_lattice()
{
  blender::WM_operatortype_append(LATTICE_OT_select_all);
  blender::WM_operatortype_append(LATTICE_OT_select_more);
  blender::WM_operatortype_append(LATTICE_OT_select_less);
  blender::WM_operatortype_append(LATTICE_OT_select_ungrouped);
  blender::WM_operatortype_append(LATTICE_OT_select_random);
  blender::WM_operatortype_append(LATTICE_OT_select_mirror);
  blender::WM_operatortype_append(LATTICE_OT_make_regular);
  blender::WM_operatortype_append(LATTICE_OT_flip);
}

void ED_keymap_lattice(wmKeyConfig *keyconf)
{
  wmKeyMap *keymap = WM_keymap_ensure(keyconf, "Lattice", SPACE_EMPTY, RGN_TYPE_WINDOW);
  keymap->poll = ED_operator_editlattice;
}

KeyBlock *ED_lattice_get_edit_shape_key(const Lattice *latt)
{
  BLI_assert(latt->editlatt);

  return BKE_keyblock_find_by_index(latt->key, latt->editlatt->shapenr - 1);
}
