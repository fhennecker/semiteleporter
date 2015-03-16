/** @file  Vertex.h
 * @brief Declaration of a vertex object 
 * @author Julie Digne
 * @date 2012-10-08
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

#ifndef VERTEX_H
#define VERTEX_H

#include <cstdlib>
#include <cstdio>
#include <iostream>
#include <set>

#include "Point.h"
#include "types.h"

class Edge;
class Facet;

using namespace std;


/**
 * @class Vertex
 * @brief Input samples to be triangulated
 * 
 * Sample point inserted as vertex in the program:
 * to begin with, it is an orphan vertex which will be aggreggated
 * during the triangulation contains topology information
 */
class Vertex : public Point
{
    /** @brief overloading operator <<
     * @param out output stream
     * @param v vertex
     * @return output stream
     */
    friend ostream& operator << (ostream& out, const Vertex& v);
  
    private : //properties
    
        /** @brief nx, ny, nz normal coordinates*/
        double m_nx, m_ny, m_nz;
        
        /** @brief set of adjacent edges*/
        Edge_set m_adjacentEdges;
        
        /** @brief set of adjacent facets*/
        Facet_set m_adjacentFacets;
        
        /** @brief vertex index of the triangulation, should be -1
         * if the vertex is an orphan*/
        int m_index;
        
        /** @brief tag: 0 if orphan, 1 if on front, 2 if inner*/
        unsigned int m_type;

    public : //constructor+destructor
    
        /** @brief default constructor*/
        Vertex();
        
        /** @brief constructor from coordinates and normal*/
        Vertex(double x, double y, double z, double nx, double ny, double nz);
          
        /** @brief default destrictor*/
        ~Vertex();
    
    public : //accessors + modifiers
   

        /** @brief add an edge to the set of edges
         * prerequisite the edge actually contains the vertex
         * @param edge edge the vertex belongs to
         * @return true if the edge was successfully added, false if the edge
         * already was in the set of edges
         */
        bool addAdjacentEdge(Edge *edge);
        
        /** @brief remove an edge from the set of adjacent edges
         * @param edge edge to remove
         */
        void removeAdjacentEdge(Edge *edge);
        
        /** @brief add a facet to the set of adjacent facets
         * prerequisite the facet actually contains the vertex
         * @param facet facet adjacent to the vertex
         * @return true if the facet was successfully added, false if the facet 
         * already was in the set of facets
         */
        bool addAdjacentFacet(Facet *facet);
         
        /** @brief remove a facet from the set of adjacent facets
         * @param facet facet to remove
         */
        void removeAdjacentFacet(Facet *facet);
        
        /** @brief get index of the vertex
         @return index
         */
        int index();
        
        /** @brief set the vertex index
         * @param index to set
         */
        void setIndex(int index);
        
        /** @brief get the set of adjacent edges
         * return the set of adjacent edges
         */
        Edge_set& adjacentEdges();
        
        /** @brief get edge linking two vertices if any
         * @param vertex test vertex
         * @return edge* if an edge links the two vertices and NULL otherwise
         */
        Edge* getLinkingEdge(Vertex *vertex);
        
        /** @brief get x normal component
         * @return x normal component nx
         */
        double nx() const;
        
        /** @brief get y normal component
         * @return y normal component ny
         */
        double ny() const;
        
        /** @brief get z normal component
         * @return z normal component nz
         * */
        double nz() const;
        
        /** @brief test if three points are compatible
         *
         * test that their normals have positive scalar product with
         * the normal to the facet formed by those three points
         * (useful to find a seed triangle)
         * @param v1 first test vertex
         * @param v2 second test vertex
         * @return true if the points are compatible
         */
        bool isCompatibleWith(const Vertex &v1, const Vertex &v2) const; 
        
        /** @brief test if a vertex is compatible with an oriented edge
         *@param e test edge
         *@return true if the edge and vertices are compatible
         */
        bool isCompatibleWith(const Edge &e) const;
          
        
        /** @brief return vertex types
         * @return type of the vertex (0,1,2)
         */
        int getType() const;
        
        /** @brief set vertex type
         * @param type (0,1,2)
         */
        void setType(int type);
        
        /** @brief update the type of a vertex according to its connectivity
         */
        void updateType();
        
        
        /** @brief test if a facet is adjacent to a vertex
         *@param facet test facet
         *@return true if the facet is adjacent
         */
        bool isAdjacent(Facet *facet);
        
        /** @brief test if two vertices are linked by a closed border with
         * three edges.
         * @param test test vertex
         * @return closure vertex or NULL
         */
         Vertex* findBorder(Vertex *test);
};



#endif
