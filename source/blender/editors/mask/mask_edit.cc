/* SPDX-FileCopyrightText: 2012 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edmask
 */

#include "BKE_context.hh"
#include "BKE_mask.h"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_clip.hh"
#include "ED_image.hh"
#include "ED_mask.hh" /* own include */
#include "ED_sequencer.hh"

#include "RNA_access.hh"

#include "mask_intern.hh" /* own include */

/* -------------------------------------------------------------------- */
/** \name Poll Functions
 * \{ */

bool ED_maskedit_poll(bContext *C)
{
  ScrArea *area = CTX_wm_area(C);
  if (area) {
    switch (area->spacetype) {
      case SPACE_CLIP:
        return ED_space_clip_maskedit_poll(C);
      case SPACE_SEQ:
        return blender::ed::vse::maskedit_poll(C);
      case SPACE_IMAGE:
        return ED_space_image_maskedit_poll(C);
    }
  }
  return false;
}

bool ED_maskedit_visible_splines_poll(bContext *C)
{
  ScrArea *area = CTX_wm_area(C);
  if (area) {
    switch (area->spacetype) {
      case SPACE_CLIP:
        return ED_space_clip_maskedit_visible_splines_poll(C);
      case SPACE_SEQ:
        return blender::ed::vse::maskedit_poll(C);
      case SPACE_IMAGE:
        return ED_space_image_maskedit_visible_splines_poll(C);
    }
  }
  return false;
}

bool ED_maskedit_mask_poll(bContext *C)
{
  ScrArea *area = CTX_wm_area(C);
  if (area) {
    switch (area->spacetype) {
      case SPACE_CLIP:
        return ED_space_clip_maskedit_mask_poll(C);
      case SPACE_SEQ:
        return blender::ed::vse::maskedit_mask_poll(C);
      case SPACE_IMAGE:
        return ED_space_image_maskedit_mask_poll(C);
    }
  }
  return false;
}

bool ED_maskedit_mask_visible_splines_poll(bContext *C)
{
  const ScrArea *area = CTX_wm_area(C);
  if (area) {
    switch (area->spacetype) {
      case SPACE_CLIP:
        return ED_space_clip_maskedit_mask_visible_splines_poll(C);
      case SPACE_SEQ:
        return blender::ed::vse::maskedit_mask_poll(C);
      case SPACE_IMAGE:
        return ED_space_image_maskedit_mask_visible_splines_poll(C);
    }
  }
  return false;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Registration
 * \{ */

void ED_operatortypes_mask()
{
  blender::WM_operatortype_append(MASK_OT_new);

  /* mask layers */
  blender::WM_operatortype_append(MASK_OT_layer_new);
  blender::WM_operatortype_append(MASK_OT_layer_remove);

  /* add */
  blender::WM_operatortype_append(MASK_OT_add_vertex);
  blender::WM_operatortype_append(MASK_OT_add_feather_vertex);
  blender::WM_operatortype_append(MASK_OT_primitive_circle_add);
  blender::WM_operatortype_append(MASK_OT_primitive_square_add);

  /* geometry */
  blender::WM_operatortype_append(MASK_OT_switch_direction);
  blender::WM_operatortype_append(MASK_OT_normals_make_consistent);
  blender::WM_operatortype_append(MASK_OT_delete);

  /* select */
  blender::WM_operatortype_append(MASK_OT_select);
  blender::WM_operatortype_append(MASK_OT_select_all);
  blender::WM_operatortype_append(MASK_OT_select_box);
  blender::WM_operatortype_append(MASK_OT_select_lasso);
  blender::WM_operatortype_append(MASK_OT_select_circle);
  blender::WM_operatortype_append(MASK_OT_select_linked_pick);
  blender::WM_operatortype_append(MASK_OT_select_linked);
  blender::WM_operatortype_append(MASK_OT_select_more);
  blender::WM_operatortype_append(MASK_OT_select_less);

  /* hide/reveal */
  blender::WM_operatortype_append(MASK_OT_hide_view_clear);
  blender::WM_operatortype_append(MASK_OT_hide_view_set);

  /* feather */
  blender::WM_operatortype_append(MASK_OT_feather_weight_clear);

  /* shape */
  blender::WM_operatortype_append(MASK_OT_slide_point);
  blender::WM_operatortype_append(MASK_OT_slide_spline_curvature);
  blender::WM_operatortype_append(MASK_OT_cyclic_toggle);
  blender::WM_operatortype_append(MASK_OT_handle_type_set);

  /* relationships */
  blender::WM_operatortype_append(MASK_OT_parent_set);
  blender::WM_operatortype_append(MASK_OT_parent_clear);

  /* Shape-keys. */
  blender::WM_operatortype_append(MASK_OT_shape_key_insert);
  blender::WM_operatortype_append(MASK_OT_shape_key_clear);
  blender::WM_operatortype_append(MASK_OT_shape_key_feather_reset);
  blender::WM_operatortype_append(MASK_OT_shape_key_rekey);

  /* layers */
  blender::WM_operatortype_append(MASK_OT_layer_move);

  /* duplicate */
  blender::WM_operatortype_append(MASK_OT_duplicate);

  /* clipboard */
  blender::WM_operatortype_append(MASK_OT_copy_splines);
  blender::WM_operatortype_append(MASK_OT_paste_splines);
}

void ED_keymap_mask(wmKeyConfig *keyconf)
{
  wmKeyMap *keymap = WM_keymap_ensure(keyconf, "Mask Editing", SPACE_EMPTY, RGN_TYPE_WINDOW);
  keymap->poll = ED_maskedit_poll;
}

void ED_operatormacros_mask()
{
  wmOperatorType *ot;
  wmOperatorTypeMacro *otmacro;

  ot = blender::WM_operatortype_append_macro("MASK_OT_add_vertex_slide",
                                             "Add Vertex and Slide",
                                             "Add new vertex and slide it",
                                             OPTYPE_UNDO | OPTYPE_REGISTER);
  ot->description = "Add new vertex and slide it";
  blender::WM_operatortype_macro_define(ot, "MASK_OT_add_vertex");
  otmacro = blender::WM_operatortype_macro_define(ot, "MASK_OT_slide_point");
  RNA_boolean_set(otmacro->ptr, "is_new_point", true);

  ot = blender::WM_operatortype_append_macro("MASK_OT_add_feather_vertex_slide",
                                             "Add Feather Vertex and Slide",
                                             "Add new vertex to feather and slide it",
                                             OPTYPE_UNDO | OPTYPE_REGISTER);
  ot->description = "Add new feather vertex and slide it";
  blender::WM_operatortype_macro_define(ot, "MASK_OT_add_feather_vertex");
  otmacro = blender::WM_operatortype_macro_define(ot, "MASK_OT_slide_point");
  RNA_boolean_set(otmacro->ptr, "slide_feather", true);

  ot = blender::WM_operatortype_append_macro("MASK_OT_duplicate_move",
                                             "Add Duplicate",
                                             "Duplicate mask and move",
                                             OPTYPE_UNDO | OPTYPE_REGISTER);
  blender::WM_operatortype_macro_define(ot, "MASK_OT_duplicate");
  otmacro = blender::WM_operatortype_macro_define(ot, "TRANSFORM_OT_translate");
  RNA_boolean_set(otmacro->ptr, "use_proportional_edit", false);
  RNA_boolean_set(otmacro->ptr, "mirror", false);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Lock-to-selection viewport preservation
 * \{ */

void ED_mask_view_lock_state_store(const bContext *C, MaskViewLockState *state)
{
  SpaceClip *space_clip = CTX_wm_space_clip(C);
  if (space_clip != nullptr) {
    ED_clip_view_lock_state_store(C, &state->space_clip_state);
  }
}

void ED_mask_view_lock_state_restore_no_jump(const bContext *C, const MaskViewLockState *state)
{
  SpaceClip *space_clip = CTX_wm_space_clip(C);
  if (space_clip != nullptr) {
    if ((space_clip->flag & SC_LOCK_SELECTION) == 0) {
      /* Early output if the editor is not locked to selection.
       * Avoids forced dependency graph evaluation here. */
      return;
    }

    /* Mask's lock-to-selection requires deformed splines to be evaluated to calculate bounds of
     * points after animation has been evaluated. The restore-no-jump type of function does
     * calculation of new offset for the view for an updated state of mask to cancel the offset out
     * by modifying locked offset. In order to do such calculation mask needs to be evaluated after
     * modification by an operator. */
    Depsgraph *depsgraph = CTX_data_ensure_evaluated_depsgraph(C);
    (void)depsgraph;

    ED_clip_view_lock_state_restore_no_jump(C, &state->space_clip_state);
  }
}

/** \} */
