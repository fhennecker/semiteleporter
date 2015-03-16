/** @file  Facet.h
 * @brief Declaration of a facet object
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


#ifndef FACET_H
#define FACET_H

#include "Point.h"
#include "Vertex.h"
#include "Edge.h"

/**
 * @class Facet
 * @brief stores a triangular facet
 *
 * A facet contains pointers to its three vertices and its
 * r-circumsphere center
 */
class Facet
{
    private :
        /** @brief vertices of the facet*/
        Vertex *m_vertex[3];

        /** @brief center of the ball that generated the facet*/
        Point m_ball_center;

    public : //constructor+destructor

        /** @brief constructor*/
        Facet();

        /** @brief constructor from a set of vertices
         * @param v1 first vertex
         * @param v2 second vertex
         * @param v3 third vertex
         */
        Facet(Vertex* v1, Vertex* v2, Vertex* v3);

        /** @brief constructor from a set of vertices
         * @param v1 first vertex
         * @param v2 second vertex
         * @param v3 third vertex
         * @param ball_center center of the empty interior
         * ball incident to the three vertices
         */
        Facet(Vertex* v1, Vertex* v2, Vertex* v3, Point &ball_center);

        /** @brief constructor from an edge and a vertex
         * prerequisite edge has at most one adjacent facet
         * @param edge edge (2 vertices to create the facet)
         * @param vertex third vertex to create the facet
         */
        Facet(Edge *edge, Vertex* vertex);

        /** @brief constructor from an edge and a vertex
         * prerequisite edge has at most one adjacent facet
         * @param edge edge
         * @param vertex vertex to link to the edge
         * @param ball_center center of the empty interior ball
         * incident to the three vertices
         */
        Facet(Edge *edge, Vertex* vertex, Point &ball_center);

        /** @brief destructor*/
        ~Facet();

    public : //accessors + modifiers

        /** @brief get facet vertex
         * @param index of the vertex in the facet
         * @return corresponding facet
         */
        Vertex* vertex(unsigned int index) const;

        /** @brief get edge opposite to vertex i
         * @param index index of the edge
         * @return edge
         */
        Edge* edge(unsigned int index) const;

        /** @brief get facet center
         * @return ball center
         */
        const Point& getBallCenter() const;

        /** @brief set Ball center
         * @param point ball center point
         */
        void setBallCenter(Point &point);

        /** @brief test if contains vertex
         * @param vertex test vertex
         * @return true if the vertex is a vertex of the facet
         */
        bool hasVertex(Vertex *vertex);
};

#endif
