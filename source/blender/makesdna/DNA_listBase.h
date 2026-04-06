/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup DNA
 * \brief These structs are the foundation for all linked lists in the library system.
 *
 * Doubly-linked lists start from a ListBase and contain elements beginning
 * with Link.
 */

#pragma once

/** Generic - all structs which are put into linked lists begin with this. */
typedef struct Link {
  struct Link *next, *prev;
} Link;

/** Simple subclass of Link. Use this when it is not worth defining a custom one. */
typedef struct LinkData {
  struct LinkData *next, *prev;
  void *data;
} LinkData;

/**
 * The basic double linked-list structure.
 *
 * \warning Never change the size/definition of this struct! The #init_structDNA
 * function (from dna_genfile.cc) uses it to compute the #pointer_size.
 */
typedef struct ListBase {
  void *first, *last;
} ListBase;

#ifdef __cplusplus

#  include "BLI_listbase_iterator.hh"

namespace blender {

/**
 * This is a thin wrapper around #ListBase to make it type-safe. It's designed to be used in DNA
 * structs. It is written as untyped #ListBase in .blend files for compatibility.
 */
template<typename T> struct ListBaseT : public ListBase {
  ListBaseTIterator<T> begin() const
  {
    return ListBaseTIterator<T>{static_cast<T *>(this->first)};
  }

  ListBaseTIterator<T> end() const
  {
    return ListBaseTIterator<T>{nullptr};
  }

  ListBaseEnumerateWrapper<T> enumerate()
  {
    return {this->first};
  }

  ListBaseEnumerateWrapper<const T> enumerate() const
  {
    return {this->first};
  }

  ListBaseMutableWrapper<T> items_mutable()
  {
    return {this->first};
  }

  ListBaseBackwardWrapper<T> items_reversed()
  {
    return {this->last};
  }

  ListBaseBackwardWrapper<const T> items_reversed() const
  {
    return {this->last};
  }

  ListBaseMutableBackwardWrapper<T> items_reversed_mutable()
  {
    return {this->last};
  }

  template<typename OtherT> const ListBaseT<OtherT> &cast() const
  {
    return *reinterpret_cast<const ListBaseT<OtherT> *>(this);
  }

  template<typename OtherT> ListBaseT<OtherT> &cast()
  {
    return *reinterpret_cast<ListBaseT<OtherT> *>(this);
  }
};

}  // namespace blender

#endif

/* 8 byte alignment! */
