/**
 * @file Edge.cpp
 * @author Julie Digne julie.digne@liris.cnrs.fr
 * @date 2012-10-08
 * @brief implementation of the edge methods declared in Edge.h
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

#include <cstdlib>
#include <cstdio>
#include <iostream>

#include "Edge.h"
#include "Vertex.h"
#include "Facet.h"
#include "utilities.h"

using namespace std;

Edge::Edge()
{
    m_src = NULL;
    m_tgt = NULL;
    m_facet1 = NULL;
    m_facet2 = NULL;
}

Edge::Edge(Vertex* src, Vertex* tgt)
{
    m_src = src;
    m_tgt = tgt;
    src->addAdjacentEdge(this);
    tgt->addAdjacentEdge(this);
    m_facet1 = NULL;
    m_facet2 = NULL;
    setType(1);
}

Edge::~Edge()
{
    m_src = NULL;
    m_tgt = NULL;
    m_facet1 = NULL;
    m_facet2 = NULL;
}

Vertex* Edge::getSource() const
{
    return m_src;
}

Vertex* Edge::getTarget() const
{
    return m_tgt;
}


Facet* Edge::getFacet1() const
{
    return m_facet1;
}

Facet* Edge::getFacet2() const
{
    return m_facet2;
}

bool Edge::addAdjacentFacet(Facet* facet)
{
    if ((m_facet1 == facet)||(m_facet2 == facet))
        return false;

    if(m_facet1 == NULL)
    {
        m_facet1 = facet;
        updateOrientation();
        setType(1);
        return true;
    }

    if(m_facet2 == NULL)
    {
        m_facet2 = facet;
        setType(2);
        return true;
    }

    std::cout<<"Already two triangles"<<endl;
    return false;

}


bool Edge::removeAdjacentFacet(Facet* facet)
{

    if(m_facet1 == facet)
    {
        m_facet1 = NULL;
        setType(1);
        return true;
    }

    if(m_facet2 == facet)
    {
        m_facet2 = NULL;
        setType(1);
        return true;
    }

    return false;

}

void Edge::updateOrientation()
{
    Vertex *opp = getOppositeVertex();

    double vx, vy, vz;

    cross_product(m_tgt->x() - m_src->x(), m_tgt->y() - m_src->y(),
                  m_tgt->z() - m_src->z(), opp->x() - m_src->x(),
                  opp->y() - m_src->y(), opp->z() - m_src->z(),
                  vx, vy, vz);
    normalize(vx, vy, vz);

    double nx, ny, nz;
    nx = m_src->nx() + m_tgt->nx() + opp->nx();
    ny = m_src->ny() + m_tgt->ny() + opp->ny();
    nz = m_src->nz() + m_tgt->nz() + opp->nz();
    normalize(nx, ny, nz);

    if(   vx * nx + vy * ny + vz * nz  < 0)
    {
        Vertex *temp = m_src;
        m_src = m_tgt;
        m_tgt = temp;
    }
}

bool Edge::hasVertex(Vertex *vertex) const
{
    if((vertex == m_src) || (vertex == m_tgt))
        return true;
    return false;
}

bool Edge::isInnerEdge() const
{
    if(m_facet2 == NULL)
        return false;
    return true;
}


int Edge::getType() const
{
    return m_type;
}

void Edge::setType(int type)
{
    m_type = type;
}


Vertex* Edge::getOppositeVertex() const
{
    if(m_facet1 == NULL)
        return NULL;
    Vertex *opp;
    for(int i = 0; i < 3; i++)
    {
        opp = m_facet1->vertex(i);
        if((opp != m_src) && (opp != m_tgt))
            return opp;
    }
    return NULL;
}
