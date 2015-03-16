/**
 * @file Edge.h
 * @author Julie Digne julie.digne@liris.cnrs.fr
 * @date 2012-10-08
 * @brief declares an edge structure (linking two vertices)
 *
 * @copyright This program is free software: you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as published 
 * by the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>. 
 */

#ifndef EDGE_H
#define EDGE_H

#include "Vertex.h"

class Facet;

/**
* @class Edge
* @brief Stores an edge with two vertices
* 
* An edge stores pointers to its two end-vertices and its two adjacent facets
* along with its type (inner, front or border)
*/
class Edge
{
  private : //properties

    /** @brief source vertex*/
    Vertex *m_src;

    /** @brief target vertex*/
    Vertex *m_tgt;

    /** @brief first adjacent facet*/
    Facet *m_facet1;

    /** @brief second adjacent facet*/
    Facet *m_facet2;


    /** @brief edge type (0: border, 1: front edge, 2: inner edge)*/
    int m_type;


    public :
    //constructor+destructor
    /** @brief Default constructor*/
    Edge();

   /** @brief Edge constructor from its endpoints
    @param src source vertex
    @param tgt target vertex
    */
   Edge(Vertex* src, Vertex* tgt);

   /** @brief Destructor*/
   ~Edge();

  public : //accessors+modifiers

   /** @brief access source vertex
    @return source vertex
    */
   Vertex* getSource() const;

   /** @brief access target vertex
   @return target vertex
   */
   Vertex* getTarget() const;

   /** @brief recompute orientation
    * to be called after adding a first facet to the edge
    */
   void updateOrientation();

   /** @brief access facet 1
    * @return facet 1
    */
   Facet* getFacet1() const;

   /** @brief access facet 2
    @return facet 2
    */
   Facet* getFacet2() const;

   /** @brief get opposite vertex: the vertex of the facet adjacent to
    * the edge and opposite to it.
    * This method only makes sense for border or front edges
    * @return opposite vertex
    */
   Vertex* getOppositeVertex() const;

   /** @brief add a facet to an edge
    * Prerequisite the facet actually contains the edge
    * @param facet the facet to add
    * @return true if the facet was successfully added, false otherwise (if the edge already had two adjacent facets)
    */
   bool addAdjacentFacet(Facet* facet);
   
   /** @brief remove a facet adjacent to an edge
    * Prerequisite the facet actually contains the edge
    * @param facet the facet to remove
    * @return true if the facet was successfully removed, false otherwise
    */
   bool removeAdjacentFacet(Facet* facet);

   /** @brief test if a vertex is a vertex of the edge
    * @param vertex test vertex
    * @return true if the vertex is either the source or target vertex of the edge
    */
   bool hasVertex(Vertex *vertex) const;

   /** @brief test if an edge is an inner edge or a front/border edge
    * @return 0 the edge is a front/border edge 1 if the edge is an inner edge
    */
   bool isInnerEdge() const;

   /** @brief return edge type
    * @return type of the edge (0,1,2)
    */
    int getType() const;

    /** @brief set edge type
     * @param type (0,1,2)
     */
    void setType(int type);
};

#endif
