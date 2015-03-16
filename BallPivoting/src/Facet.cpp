/** @file  Facet.cpp
 * @brief implementation of the facet methods declared in Facet.h
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

#include "Facet.h"
#include "Edge.h"
#include "Vertex.h"


Facet::Facet()
{
    for(int i=0;i<3;i++)
        m_vertex[i] = NULL;
}

Facet::Facet(Vertex* v0, Vertex* v1, Vertex* v2)
{
    m_vertex[0] = v0;
    m_vertex[1] = v1;
    m_vertex[2] = v2;

    Edge *e0 = v0->getLinkingEdge(v1);
    if(e0 == NULL)
    {
        e0 = new Edge(v0, v1);
    }
    e0->addAdjacentFacet(this);

    Edge *e1 = v1->getLinkingEdge(v2);
    if(e1 == NULL)
    {
        e1 = new Edge(v1, v2);
    }
    e1->addAdjacentFacet(this);

    Edge *e2 = v2->getLinkingEdge(v0);
    if(e2 == NULL)
    {
        e2 = new Edge(v2, v0);
    }
    e2->addAdjacentFacet(this);

    for(int i= 0; i < 3; i++)
    {
        m_vertex[i]->addAdjacentFacet(this);
        m_vertex[i]->updateType();
    }
}

Facet::Facet(Vertex* v0, Vertex* v1, Vertex* v2, Point &ball_center)
{
    m_vertex[0] = v0;
    m_vertex[1] = v1;
    m_vertex[2] = v2;
    m_ball_center = ball_center;

    Edge *e0 = v0->getLinkingEdge(v1);
    if(e0 == NULL)
    {
        e0 = new Edge(v0,v1);
    }
    e0->addAdjacentFacet(this);

    Edge *e1 = v1->getLinkingEdge(v2);
    if(e1 == NULL)
    {
        e1 = new Edge(v1,v2);
    }
    e1->addAdjacentFacet(this);

    Edge *e2 = v2->getLinkingEdge(v0);
    if(e2 == NULL)
    {
        e2 = new Edge(v2, v0);
    }
    e2->addAdjacentFacet(this);

    for(unsigned int i = 0; i < 3; i++)
    {
        m_vertex[i]->addAdjacentFacet(this);
        m_vertex[i]->updateType();
    }
}

Facet::Facet(Edge* edge, Vertex* vertex)
{
    Vertex *src = edge->getSource();
    Vertex *tgt = edge->getTarget();

    m_vertex[0] = src;
    m_vertex[1] = vertex;
    m_vertex[2] = tgt;


    edge->addAdjacentFacet(this);


    for(int i = 0; i < 2; i++)
    {
        Edge *e = m_vertex[i]->getLinkingEdge(m_vertex[i+1]);
        if(e == NULL)
        {
            e = new Edge(m_vertex[i], m_vertex[i+1]);
        }
        e->addAdjacentFacet(this);
    }

    for(int i= 0; i < 3; i++)
    {
        m_vertex[i]->addAdjacentFacet(this);
        m_vertex[i]->updateType();

    }
}

Facet::Facet(Edge* edge, Vertex* vertex, Point &ball_center)
{
    Vertex *src = edge->getSource();
    Vertex *tgt = edge->getTarget();

    m_vertex[0] = src;
    m_vertex[1] = vertex;
    m_vertex[2] = tgt;
    m_ball_center = ball_center;

    edge->addAdjacentFacet(this);

    for(int i = 0; i < 2; ++i)
    {
        Edge *e = m_vertex[i]->getLinkingEdge(m_vertex[i+1]);
        if(e == NULL)
        {
            e = new Edge(m_vertex[i], m_vertex[i+1]);
        }
        e->addAdjacentFacet(this);
    }

    for(int i= 0; i < 3; ++i)
    {
        m_vertex[i]->addAdjacentFacet(this);
        m_vertex[i]->updateType();
    }
}

Facet::~Facet()
{
    for(unsigned int i=0;i<3;++i)
        m_vertex[i]->removeAdjacentFacet(this);

    for(int i = 0; i < 2; ++i)
    {
        Edge *e = m_vertex[i]->getLinkingEdge(m_vertex[i+1]);

        if((e->getFacet2() == NULL)&&(e->getFacet2()==NULL))
        {
            m_vertex[i]->removeAdjacentEdge(e);
            m_vertex[i+1]->removeAdjacentEdge(e);
            delete e;
            e=NULL;
        }
        else
        {
            e->removeAdjacentFacet(this);
        }
    }
}

Vertex* Facet::vertex(unsigned int i) const
{
    unsigned int index = i %3;
    return m_vertex[index];
}

Edge* Facet::edge(unsigned int i) const
{
    unsigned int i1 = (i+1) %3;
    unsigned int i2 = (i+2) %3;
    return m_vertex[i1]->getLinkingEdge(m_vertex[i2]);
}

const Point& Facet::getBallCenter() const
{
    return m_ball_center;
}

void Facet::setBallCenter(Point& point)
{
    m_ball_center = point;
}

bool Facet::hasVertex(Vertex* v)
{
    if((m_vertex[0] == v)||(m_vertex[1] == v)||(m_vertex[2] == v))
        return true;
    else
        return false;
}

