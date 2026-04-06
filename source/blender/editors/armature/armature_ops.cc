/* SPDX-FileCopyrightText: 2009 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edarmature
 */

#include "RNA_access.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_armature.hh"
#include "ED_screen.hh"

#include "armature_intern.hh"

/* ************************** registration **********************************/

void ED_operatortypes_armature()
{
  /* Both operators `ARMATURE_OT_*` and `POSE_OT_*` are registered here. */

  /* EDIT ARMATURE */
  blender::WM_operatortype_append(ARMATURE_OT_bone_primitive_add);

  blender::WM_operatortype_append(ARMATURE_OT_align);
  blender::WM_operatortype_append(ARMATURE_OT_calculate_roll);
  blender::WM_operatortype_append(ARMATURE_OT_roll_clear);
  blender::WM_operatortype_append(ARMATURE_OT_switch_direction);
  blender::WM_operatortype_append(ARMATURE_OT_subdivide);

  blender::WM_operatortype_append(ARMATURE_OT_parent_set);
  blender::WM_operatortype_append(ARMATURE_OT_parent_clear);

  blender::WM_operatortype_append(ARMATURE_OT_select_all);
  blender::WM_operatortype_append(ARMATURE_OT_select_mirror);
  blender::WM_operatortype_append(ARMATURE_OT_select_more);
  blender::WM_operatortype_append(ARMATURE_OT_select_less);
  blender::WM_operatortype_append(ARMATURE_OT_select_hierarchy);
  blender::WM_operatortype_append(ARMATURE_OT_select_linked);
  blender::WM_operatortype_append(ARMATURE_OT_select_linked_pick);
  blender::WM_operatortype_append(ARMATURE_OT_select_similar);
  blender::WM_operatortype_append(ARMATURE_OT_shortest_path_pick);

  blender::WM_operatortype_append(ARMATURE_OT_delete);
  blender::WM_operatortype_append(ARMATURE_OT_dissolve);
  blender::WM_operatortype_append(ARMATURE_OT_duplicate);
  blender::WM_operatortype_append(ARMATURE_OT_symmetrize);
  blender::WM_operatortype_append(ARMATURE_OT_extrude);
  blender::WM_operatortype_append(ARMATURE_OT_hide);
  blender::WM_operatortype_append(ARMATURE_OT_reveal);
  blender::WM_operatortype_append(ARMATURE_OT_click_extrude);
  blender::WM_operatortype_append(ARMATURE_OT_fill);
  blender::WM_operatortype_append(ARMATURE_OT_separate);
  blender::WM_operatortype_append(ARMATURE_OT_split);

  blender::WM_operatortype_append(ARMATURE_OT_autoside_names);
  blender::WM_operatortype_append(ARMATURE_OT_flip_names);

  blender::WM_operatortype_append(ARMATURE_OT_collection_add);
  blender::WM_operatortype_append(ARMATURE_OT_collection_remove);
  blender::WM_operatortype_append(ARMATURE_OT_collection_move);
  blender::WM_operatortype_append(ARMATURE_OT_collection_assign);
  blender::WM_operatortype_append(ARMATURE_OT_collection_create_and_assign);
  blender::WM_operatortype_append(ARMATURE_OT_collection_unassign);
  blender::WM_operatortype_append(ARMATURE_OT_collection_unassign_named);
  blender::WM_operatortype_append(ARMATURE_OT_collection_select);
  blender::WM_operatortype_append(ARMATURE_OT_collection_deselect);

  blender::WM_operatortype_append(ARMATURE_OT_move_to_collection);
  blender::WM_operatortype_append(ARMATURE_OT_assign_to_collection);

  /* POSE */
  blender::WM_operatortype_append(POSE_OT_hide);
  blender::WM_operatortype_append(POSE_OT_reveal);

  blender::WM_operatortype_append(POSE_OT_armature_apply);
  blender::WM_operatortype_append(POSE_OT_visual_transform_apply);

  blender::WM_operatortype_append(POSE_OT_rot_clear);
  blender::WM_operatortype_append(POSE_OT_loc_clear);
  blender::WM_operatortype_append(POSE_OT_scale_clear);
  blender::WM_operatortype_append(POSE_OT_transforms_clear);
  blender::WM_operatortype_append(POSE_OT_user_transforms_clear);

  blender::WM_operatortype_append(POSE_OT_copy);
  blender::WM_operatortype_append(POSE_OT_paste);

  blender::WM_operatortype_append(POSE_OT_select_all);

  blender::WM_operatortype_append(POSE_OT_select_parent);
  blender::WM_operatortype_append(POSE_OT_select_hierarchy);
  blender::WM_operatortype_append(POSE_OT_select_linked);
  blender::WM_operatortype_append(POSE_OT_select_linked_pick);
  blender::WM_operatortype_append(POSE_OT_select_constraint_target);
  blender::WM_operatortype_append(POSE_OT_select_grouped);
  blender::WM_operatortype_append(POSE_OT_select_mirror);

  blender::WM_operatortype_append(POSE_OT_paths_calculate);
  blender::WM_operatortype_append(POSE_OT_paths_update);
  blender::WM_operatortype_append(POSE_OT_paths_clear);
  blender::WM_operatortype_append(POSE_OT_paths_range_update);

  blender::WM_operatortype_append(POSE_OT_autoside_names);
  blender::WM_operatortype_append(POSE_OT_flip_names);

  blender::WM_operatortype_append(POSE_OT_rotation_mode_set);

  blender::WM_operatortype_append(POSE_OT_quaternions_flip);

  blender::WM_operatortype_append(POSE_OT_propagate);

  /* POSELIB */
  blender::WM_operatortype_append(POSELIB_OT_apply_pose_asset);
  blender::WM_operatortype_append(POSELIB_OT_blend_pose_asset);

  /* POSE SLIDING */
  blender::WM_operatortype_append(POSE_OT_push);
  blender::WM_operatortype_append(POSE_OT_relax);
  blender::WM_operatortype_append(POSE_OT_blend_with_rest);
  blender::WM_operatortype_append(POSE_OT_breakdown);
  blender::WM_operatortype_append(POSE_OT_blend_to_neighbors);
}

void ED_operatormacros_armature()
{
  wmOperatorType *ot;
  wmOperatorTypeMacro *otmacro;

  ot = blender::WM_operatortype_append_macro(
      "ARMATURE_OT_duplicate_move",
      "Duplicate",
      "Make copies of the selected bones within the same armature and move them",
      OPTYPE_UNDO | OPTYPE_REGISTER);
  blender::WM_operatortype_macro_define(ot, "ARMATURE_OT_duplicate");
  otmacro = blender::WM_operatortype_macro_define(ot, "TRANSFORM_OT_translate");
  RNA_boolean_set(otmacro->ptr, "use_proportional_edit", false);

  ot = blender::WM_operatortype_append_macro("ARMATURE_OT_extrude_move",
                                    "Extrude",
                                    "Create new bones from the selected joints and move them",
                                    OPTYPE_UNDO | OPTYPE_REGISTER);
  otmacro = blender::WM_operatortype_macro_define(ot, "ARMATURE_OT_extrude");
  RNA_boolean_set(otmacro->ptr, "forked", false);
  otmacro = blender::WM_operatortype_macro_define(ot, "TRANSFORM_OT_translate");
  RNA_boolean_set(otmacro->ptr, "use_proportional_edit", false);

  /* XXX would it be nicer to just be able to have standard extrude_move,
   * but set the forked property separate?
   * that would require fixing a properties bug #19733. */
  ot = blender::WM_operatortype_append_macro("ARMATURE_OT_extrude_forked",
                                    "Extrude Forked",
                                    "Create new bones from the selected joints and move them",
                                    OPTYPE_UNDO | OPTYPE_REGISTER);
  otmacro = blender::WM_operatortype_macro_define(ot, "ARMATURE_OT_extrude");
  RNA_boolean_set(otmacro->ptr, "forked", true);
  otmacro = blender::WM_operatortype_macro_define(ot, "TRANSFORM_OT_translate");
  RNA_boolean_set(otmacro->ptr, "use_proportional_edit", false);
}

void ED_keymap_armature(wmKeyConfig *keyconf)
{
  wmKeyMap *keymap;

  /* Armature ------------------------ */
  /* only set in editmode armature, by space_view3d listener */
  keymap = WM_keymap_ensure(keyconf, "Armature", SPACE_EMPTY, RGN_TYPE_WINDOW);
  keymap->poll = ED_operator_editarmature;

  /* Pose ------------------------ */
  /* only set in posemode, by space_view3d listener */
  keymap = WM_keymap_ensure(keyconf, "Pose", SPACE_EMPTY, RGN_TYPE_WINDOW);
  keymap->poll = ED_operator_posemode;
}
