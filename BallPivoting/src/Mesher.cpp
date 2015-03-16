/**
 * @file Mesher.cpp
 * @brief defines methods for building a surface mesh from points stored in an 
 * octree these methods are declared in Mesher.h
 * @author Julie Digne julie.digne@liris.cnrs.fr
 * @date 2012/10/17
 * @copyright This file implements an algorithm possibly linked to the patent 
 * US6968299B1.
 * This file is made available for the exclusive aim of serving as
 * scientific tool to verify the soundness and completeness of the
 * algorithm description. Compilation, execution and redistribution
 * of this file may violate patents rights in certain countries.
 * The situation being different for every country and changing
 * over time, it is your responsibility to determine which patent
 * rights restrictions apply to you before you compile, use,
 * modify, or redistribute this file. A patent lawyer is qualified
 * to make this determination.
 * If and only if they don't conflict with any patent terms, you
 * can benefit from the following license terms attached to this
 * file.
 * This program is free software: you can redistribute it and/or
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
#include "Mesher.h"
#include "OctreeIterator.h"
#include <cstdlib>
#include <cmath>
#include <cassert>
#ifndef USE_CLANG
    #include <omp.h>
#endif
#include <sstream>

const double PI = 3.1415926535;

using namespace std;

Mesher::Mesher()
{
    m_octree = NULL;
    m_iterator = NULL;
    m_nfacets = 0;
    m_nvertices = 0;
}

Mesher::Mesher(Octree* octree, OctreeIterator* iterator)
{
    m_octree = octree;
    m_iterator = iterator;
    m_ball_radius = iterator->getR();
    m_sq_ball_radius = m_ball_radius * m_ball_radius;
    m_nfacets = 0;
    m_nvertices = 0;
}


Mesher::~Mesher()
{
    m_octree = NULL;
    m_iterator = NULL;
    m_edge_front.clear();
    m_border_edges.clear();

    Facet_star_list::iterator fi;
    for(fi = m_facets.begin(); fi != m_facets.end(); ++fi)
    {
        delete *fi;
        *fi = NULL;
    }

    m_facets.clear();
    m_vertices.clear();
    m_nfacets = 0;
    m_nvertices = 0;
}



void Mesher::setBallRadius(double r)
{
    m_ball_radius = r;
    m_sq_ball_radius = r*r;
}

double Mesher::getBallRadius() const
{
    return m_ball_radius;
}

double Mesher::getSquareBallRadius() const
{
    return m_sq_ball_radius;
}

unsigned int Mesher::nVertices() const
{
    return m_nvertices;
}


unsigned int Mesher::nFacets() const
{
    return m_nfacets;
}

unsigned int Mesher::nFrontEdges() const
{
    return (unsigned int) m_edge_front.size();
}

unsigned int Mesher::nBorderEdges() const
{
    return (unsigned int) m_border_edges.size();
}


void Mesher::reconstruct()
{
    std::cout<<"***********Ball radius "<<m_ball_radius
             <<" ***********"<<std::endl;

    if(m_edge_front.empty())
    {
        bool ok = findSeedTriangle();
        if(!ok)
            std::cout<<"No seed triangle found, no triangulation done!"
            <<std::endl;
    }
    else
    {
        expandTriangulation();
    }
}


void Mesher::reconstruct(std::list< double >& radii)
{
    std::cout<<"single threaded reconstruction"<<std::endl;
    while(! radii.empty())
    {
        double radius = radii.front();

        changeRadius(radius);
        reconstruct();
        radii.pop_front();
    }
}


void Mesher::changeRadius(double radius)
{
    setBallRadius(radius);
    Edge_star_list::iterator ei = m_border_edges.begin();
    while(ei != m_border_edges.end())
    {
        Edge *e = *ei;
        Facet *f = e->getFacet1();

        Point center;
        if(emptyBallConfiguration(f->vertex(0), f->vertex(1),
            f->vertex(2),center))
        {
            e->setType(1);
            m_edge_front.push_back(e);
            ei = m_border_edges.erase(ei);
            continue;
        }
        ++ei;
    }
}


bool Mesher::findSeedTriangle()
{
    bool found = false;
    OctreeNode *node = m_octree->getRoot();
    findSeedTriangle(node, found);
    return found;
}

void Mesher::findSeedTriangle(OctreeNode* node, bool &found)
{
    if( node->getDepth() != 0)
    {
        for(unsigned int i = 0; i<8; i++)
        {
            if(node->getChild(i) != NULL)
                findSeedTriangle(node->getChild(i), found);
        }
    }
    else if( node->getNpts() != 0)
    {
        Vertex_list::iterator pi = node->points_begin();
        while( pi != node->points_end())
        {
            //test if pi is an orphan vertex or active vertex
            if(pi->getType() ==0)
            {
                if(trySeed(*pi))
                {
                    found = true;
                    expandTriangulation();
                }
            }
            ++pi;
        }
    }
}



bool Mesher::trySeed(Vertex& v)
{

    Neighbor_star_map neighbors;
    m_iterator->setR(2.0 * m_ball_radius);
    m_iterator->getSortedNeighbors(v, neighbors);
    m_iterator->setR(m_ball_radius);

    if(neighbors.size()<3)
        return false;

    Neighbor_iterator ni = neighbors.begin();
    while(ni != neighbors.end())
    {
        Vertex &vtest = *(ni->second);
        if( (vtest.getType() != 0) || (&vtest == &v) )
        {
            ++ni;
            continue;
        }

        Neighbor_iterator nj = ni;
        ++nj;

        Vertex *candidate = NULL;
        Point center;
        while(nj != neighbors.end())
        {
            if(tryTriangleSeed(&v, &vtest, nj->second, neighbors, center))
            {
                candidate = nj->second;
                break;
            }
            ++nj;
        }

        if(candidate != NULL)
        {
            Edge *e1 = v.getLinkingEdge(candidate);
            Edge *e2 = vtest.getLinkingEdge(candidate);
            Edge *e3 = v.getLinkingEdge(&vtest);

            if( ((e1!=NULL)&&(e1->getType()!=1))
                ||((e2!=NULL)&&(e2->getType()!=1))
                ||((e3!=NULL)&&(e3->getType()!=1)) )
            {
                ++ni;
                continue;
            }

            Facet *facet = new Facet(&v, &vtest, candidate, center);
            addFacet(facet);

            if(m_nfacets % 10000 == 0)
            std::cout<<m_nvertices<<" vertices. "<<m_nfacets<<" facets. "
            <<m_edge_front.size()<<" front edges. "
            <<m_border_edges.size()<<" border edges."<<std::endl;


            e1 = v.getLinkingEdge(candidate);
            e2 = vtest.getLinkingEdge(candidate);
            e3 = v.getLinkingEdge(&vtest);

            if(e1->getType() == 1)
                m_edge_front.push_front(e1);
            if(e2->getType() == 1)
                m_edge_front.push_front(e2);
            if(e3->getType() == 1)
                m_edge_front.push_front(e3);

            if(m_edge_front.size() > 0)
                return true;
        }
        ++ni;
    }
    return false;
}


bool Mesher::tryTriangleSeed(Vertex* v1, Vertex* v2, Vertex *v3, 
                             Neighbor_star_map &neighbors,
                             Point &center) const
{
    if((v3->getType() != 0) || ( !v3->isCompatibleWith(*v1, *v2)))
        return false;

    Edge *e1 = v1->getLinkingEdge(v3);
    Edge *e2 = v2->getLinkingEdge(v3);
    if(  ((e1!=NULL)&&(e1->getType()==2))
        || ((e2!=NULL)&&(e2->getType()==2)))
        return false;

    m_iterator->setR(m_ball_radius);
    if(! computeBallCenter(*v1, *v2, *v3, center))
        return false;

    Neighbor_iterator ni;
    for(ni = neighbors.begin(); ni != neighbors.end(); ++ni)
    {
        Vertex *v = ni->second;
        if((v == v1)||(v == v2)||(v == v3))
            continue;
        if( dist2(center,*v) < m_sq_ball_radius - 1e-16)
            return false;
    }
    return true;
}


bool Mesher::emptyBallConfiguration(Vertex* v1, Vertex* v2, Vertex* v3,
                                    Point & center) const
{
    m_iterator->setR(m_ball_radius);
    if(! computeBallCenter(*v1, *v2, *v3, center))
        return false;

    std::set<Vertex*> facet_vertices;

    facet_vertices.insert(v1);
    facet_vertices.insert(v2);
    facet_vertices.insert(v3);

    return m_iterator->containsOnly(center, facet_vertices);
}

bool Mesher::checkEmptyBallConfiguration(Vertex* v1, Vertex* v2, Vertex* v3,
                                         const Vertex_star_list &neighbors,
                                         const Point & center) const
{
   Vertex_star_list::const_iterator ni;
   for(ni = neighbors.begin() ; ni != neighbors.end(); ++ni)
   {
       const Vertex *v = *ni;
       if((v == v1)||(v == v2)||(v == v3))
           continue;
       if(dist2(*v,center)<m_sq_ball_radius - 1e-16)
           return false;
   }
    return true;
}

bool Mesher::computeBallCenter(const Vertex &v1, const Vertex &v2,
                               const Vertex &v3, Point &center) const
{
    //compute the circumcenter barycentric coordinates
    double c = dist2(v2, v1);
    double b = dist2(v1, v3);
    double a = dist2(v3, v2);
    double alpha = a *( b + c - a);
    double beta  = b *( a + c - b);
    double gamma = c *( a + b - c);
    double temp = alpha + beta + gamma;

    if(temp<1e-30)//aligned case
	    return false;


    alpha = alpha / temp;
    beta  =  beta / temp;
    gamma = gamma / temp;


    //computing the triangle circumcircle center
    double x = alpha * v1.x() + beta * v2.x() + gamma * v3.x();
    double y = alpha * v1.y() + beta * v2.y() + gamma * v3.y();
    double z = alpha * v1.z() + beta * v2.z() + gamma * v3.z();

    //computing the radius of the circumcircle
    double sq_circumradius = a * b * c;


    a = sqrt(a);
    b = sqrt(b);
    c = sqrt(c);

    sq_circumradius = sq_circumradius /
          ( (a + b + c) * (b + c - a) * (c + a - b) * (a + b - c) );

    //compute the ortogonal distance from the hypothetic center to the triangle
    double height = m_sq_ball_radius - sq_circumradius;

    //compute the normal of the three points
    double nx,ny,nz = 0;

    if(height >= 0.0)
    {
        computeNormal(v1, v2, v3, nx, ny, nz);
        height = sqrt(height);
        center = Point( x + height*nx, y + height*ny, z + height*nz);
        return true;
    }
    return false;
}

void Mesher::computeNormal(const Vertex& v1, const Vertex& v2, const Vertex& v3,
                           double &nx, double &ny, double &nz) const
{
    cross_product( v2.x() - v1.x(), v2.y() - v1.y(), v2.z() - v1.z(),
		   v3.x() - v1.x(), v3.y() - v1.y(), v3.z() - v1.z(),
		   nx, ny, nz);
    normalize(nx,ny,nz);

    double mnx = v1.nx() + v2.nx() + v3.nx();
    double mny = v1.ny() + v2.ny() + v3.ny();
    double mnz = v1.nz() + v2.nz() + v3.nz();

    normalize(mnx,mny,mnz);

    if(nx*mnx + ny*mny + nz*mnz <0)
    {
      nx = -nx;
      ny = -ny;
      nz = -nz;
    }
}



void Mesher::expandTriangulation()
{
    while(! m_edge_front.empty() )
    {
        Edge *edge = m_edge_front.front();
        m_edge_front.pop_front();


        if(edge->getType() != 1)
            continue;

        Point center;
        Vertex *candidate = findCandidateVertex(edge, center);

        if((candidate == NULL) || (candidate->getType()==2)
            ||(! candidate->isCompatibleWith(*edge)))
        {
            edge->setType(0);
            m_border_edges.push_back(edge);
            continue;
        }

        Edge *e1 = candidate->getLinkingEdge(edge->getSource());
        Edge *e2 = candidate->getLinkingEdge(edge->getTarget());

        if( ((e1!=NULL) && (e1->getType()!=1))
            || ((e2!=NULL) && (e2->getType()!=1)))
        {
            edge->setType(0);
            m_border_edges.push_back(edge);
            continue;
        }

        Facet * facet = new Facet(edge, candidate, center);
        addFacet(facet);

        e1 = candidate->getLinkingEdge(edge->getSource());
        e2 = candidate->getLinkingEdge(edge->getTarget());

        if(e1->getType() == 1)
            m_edge_front.push_front(e1);

        if(e2->getType() == 1)
            m_edge_front.push_front(e2);

        if(m_nfacets % 10000 == 0)
            std::cout<<m_nvertices<<" vertices. "<<m_nfacets<<" facets. "
            <<m_edge_front.size()<<" front edges. "
            <<m_border_edges.size()<<" border edges."<<std::endl;
    }
}

Vertex* Mesher::findCandidateVertex(Edge *edge, Point &candidate_ball_center)
{
    Vertex *src = edge->getSource();
    Vertex *tgt = edge->getTarget();

    Point mp = midpoint(*src, *tgt);
    Vertex_star_list neighbors;

    double d = m_ball_radius + sqrt( m_sq_ball_radius - dist2(mp, *src) );
    m_iterator->setR(d);
    m_iterator->getNeighbors(mp,neighbors);
    m_iterator->setR(m_ball_radius);

    Facet *facet = edge->getFacet1();
    const Point &center = facet->getBallCenter();

    Vertex * opp = edge->getOppositeVertex();

    double vx,vy,vz;
    vx = tgt->x()-src->x();
    vy = tgt->y()-src->y();
    vz = tgt->z()-src->z();

    normalize(vx,vy,vz);

    double ax,ay,az;
    ax = center.x() - mp.x();
    ay = center.y() - mp.y();
    az = center.z() - mp.z();
    normalize(ax,ay,az);


    Vertex *candidate = NULL;
    double min_angle = 2.0 * PI;

    for(Vertex_star_list::const_iterator vi = neighbors.begin();
        vi != neighbors.end(); ++vi)
    {
        Vertex *v = *vi;
        if(( v == src)||(v == tgt)||(v == opp))
          continue;

        Point new_center;
        if(! computeBallCenter(*src, *tgt, *v, new_center))
          continue;

        //angle computation
        double bx,by,bz;
        bx = new_center.x() - mp.x();
        by = new_center.y() - mp.y();
        bz = new_center.z() - mp.z();
        normalize(bx,by,bz);

        double cosinus = ax * bx + ay * by + az * bz;

        cosinus = 1.0 < cosinus ? 1.0 : cosinus;
        cosinus = -1.0 > cosinus ? -1.0 : cosinus;

        double angle = acos(cosinus);

        double cpx,cpy,cpz;
        cross_product(ax, ay, az, bx, by, bz, cpx, cpy, cpz);

        if( cpx * vx + cpy * vy + cpz * vz < 0)
          angle = 2.0 * PI - angle;

        if(angle > min_angle)
          continue;

        if(!checkEmptyBallConfiguration(src, tgt, v, neighbors, new_center))
	        continue;

        min_angle = angle;
        candidate = v;
        candidate_ball_center = new_center;
    }
    return candidate;
}


void Mesher::addFacet(Facet* f)
{
    addVertex( f->vertex(0) );
    addVertex( f->vertex(1) );
    addVertex( f->vertex(2) );

    m_facets.push_back(f);
    m_nfacets++;
}


void Mesher::addVertex(Vertex* v)
{
    if(v->index() != -1)
        return;

    v->setIndex(m_nvertices);
    m_vertices.push_back(v);
    m_nvertices++;
}


std::list< Vertex* >::const_iterator Mesher::vertices_begin() const
{
    return m_vertices.begin();
}

std::list< Vertex* >::const_iterator Mesher::vertices_end() const
{
    return m_vertices.end();
}
std::list< Facet* >::const_iterator Mesher::facets_begin() const
{
    return m_facets.begin();
}

std::list< Facet* >::const_iterator Mesher::facets_end() const
{
    return m_facets.end();
}

void Mesher::fillHoles()
{
    Edge_star_iterator ei= m_border_edges.begin();
    while(ei != m_border_edges.end())
    {
        //during the filling process border edges become inner edges
        //hence the following check
        if((*ei)->getType() != 0)
        {
	        ei = m_border_edges.erase(ei);
	        continue;
        }
        Vertex *src = (*ei)->getSource();
        Vertex *tgt = (*ei)->getTarget();

        Vertex *v = src->findBorder(tgt);

        //if no oriented border links tgt to src (order is important since
        //edges of the front are oriented consistently all over the front)
        if(v == NULL)
        {
	        ++ei;
	        continue;
        }

        Facet *f = new Facet(src,tgt,v);
        addFacet(f);
        ei = m_border_edges.erase(ei);
    }
}



void Mesher::parallelReconstruct(std::list< double >& radii)
{
    OctreeNode *root = m_octree->getRoot();
    unsigned int depth = m_iterator->getDepth();

    const double d = 2.1 * radii.back();//largest chosen radius
    depth = (unsigned int)(m_octree->getDepth()
    - floor( log2( m_octree->getSize() / (1.5 * d) )));

    if(depth < m_octree->getDepth() - 3)
        depth = m_octree->getDepth() - 3 ;
    else if(depth > m_octree->getDepth() )
        depth = m_octree->getDepth();

    std::cout<<"Processing depth "<<depth<<" ; size "
             <<m_octree->getSize()/(double)pow2(m_octree->getDepth()-depth)
             <<" ; dilatation radius "<<d<<std::endl;

    OctreeNode_collection node_collection;
    m_octree->getNodes(depth, root, node_collection);

    std::list<double>::iterator ri = radii.begin();
    int init = 0;
    while(ri != radii.end())
    {
        for(unsigned int i = 0; i < 8; ++i)
        {
#ifndef USE_CLANG
           #pragma omp parallel for default(shared)
#endif
            for(int j = 0; j < (int)node_collection[i].size(); ++j)
            {
                OctreeNode *node = node_collection[i][j];
                OctreeIterator iter(m_octree);
                Mesher mesher(m_octree, &iter);

                if(init>0)
                    mesher.collectBorderEdges(node);

                mesher.changeRadius(*ri);
                if(init == 0)
                    mesher.reconstructAroundNode(node, d);
                else
                    mesher.expandTriangulationAroundNode(node,d);

#ifndef USE_CLANG
                #pragma omp critical
                {
#endif //USE_CLANG
                    merge(mesher);
#ifndef USE_CLANG
                }
#endif //USE_CLANG
            }
            std::cout<<"Nodes "<<i<<"/7 ; Nvertices: "<<nVertices()
                     <<" ; Nfacets "<<nFacets()
                     <<" ; Front "<<nFrontEdges()<<"."<<std::endl;
        }
        ++ri;
        ++init;
    }

    if(radii.size()>1)
    {
        std::cout<<"Remaining front edges "<<m_edge_front.size()<<std::endl;
        setBallRadius(radii.back());
        expandTriangulation();
    }
}




void Mesher::findSeedTriangle(OctreeNode* containment_node, OctreeNode* node,
                                double d, bool& found)
{
    if( node->getDepth() != 0)
    {
        for(unsigned int i = 0; i<8; i++)
        {
            if(node->getChild(i) != NULL)
                findSeedTriangle(containment_node, node->getChild(i), d, found);
        }
    }
    else if( node->getNpts() != 0)
    {
        Vertex_list::iterator pi = node->points_begin();
        while( pi != node->points_end())
        {
            if(pi->getType()==1)
            {
                Edge_set &edges = pi->adjacentEdges();
                Edge_set::iterator ei;
                for( ei = edges.begin(); ei != edges.end(); ++ei)
                    if((*ei)->getType() == 1)
                        m_edge_front.push_front(*ei);
                    expandTriangulationAroundNode(containment_node, d);
            }
            else if(pi->getType() ==0)
            {
                if(trySeed(*pi, containment_node, d))
                {
                    found = true;
                    expandTriangulationAroundNode(containment_node, d);
                    continue;
                }
            }
            ++pi;
        }
    }
}

bool Mesher::trySeed(Vertex& v, OctreeNode *containment_node, double d)
{

    Neighbor_star_map neighbors;
    m_iterator->setR(2.0 * m_ball_radius);
    m_iterator->getSortedNeighbors(v, neighbors);
    m_iterator->setR(m_ball_radius);

    if(neighbors.size()<3)
        return false;

    Neighbor_iterator ni = neighbors.begin();
    while(ni != neighbors.end())
    {
        Vertex &vtest = *(ni->second);
        if( (vtest.getType() != 0) || (&vtest == &v)
            || (! containment_node->isInside(vtest, d)) )
        {
            ++ni;
            continue;
        }

        Neighbor_iterator nj = ni;
        ++nj;

        Vertex *candidate = NULL;
        Point center;
        while(nj != neighbors.end())
        {
            if(tryTriangleSeed(&v, &vtest, nj->second, neighbors, center))
            {
                candidate = nj->second;
                break;
            }
            ++nj;
        }


        if(candidate == NULL)
        {
            Edge *e = v.getLinkingEdge(&vtest);
            if((e!=NULL)&&(e->getType()==1))
                m_edge_front.push_front(e);
        }
        else if(containment_node->isInside(*candidate, d))
        {
            Edge *e1 = v.getLinkingEdge(candidate);
            Edge *e2 = vtest.getLinkingEdge(candidate);
            Edge *e3 = v.getLinkingEdge(&vtest);

            if( ((e1!=NULL)&&(e1->getType()!=1))
                ||((e2!=NULL)&&(e2->getType()!=1))
                ||((e3!=NULL)&&(e3->getType()!=1)) )
            {
                ++ni;
                continue;
            }

            Facet *facet = new Facet(&v, &vtest, candidate, center);
            addFacet(facet);
            
            e1 = v.getLinkingEdge(candidate);
            e2 = vtest.getLinkingEdge(candidate);
            e3 = v.getLinkingEdge(&vtest);

            if(e1->getType() == 1)
                m_edge_front.push_front(e1);
            if(e2->getType() == 1)
                m_edge_front.push_front(e2);
            if(e3->getType() == 1)
                m_edge_front.push_front(e3);

            if(m_edge_front.size() > 0)
                return true;
        }
        ++ni;
    }
    if(m_edge_front.size() > 0)
        return true;
    return false;
}



void Mesher::reconstructAroundNode(OctreeNode *containment_node, double d)
{
    if(!m_edge_front.empty())
        expandTriangulationAroundNode(containment_node, d);

    bool found = false;
    findSeedTriangle(containment_node, containment_node, d, found);
}

void Mesher::expandTriangulationAroundNode(OctreeNode* containment_node,
                                           double d)
{
    while(! m_edge_front.empty() )
    {
        Edge *edge = m_edge_front.front();
        m_edge_front.pop_front();

        if(edge->getType() != 1)
            continue;

        Point center;
        Vertex *candidate = findCandidateVertex(edge, center);

        if((candidate == NULL) || (candidate->getType()==2)
            ||  (! candidate->isCompatibleWith(*edge)))
        {
            edge->setType(0);
            m_border_edges.push_back(edge);
            continue;
        }

        Edge *e1 = candidate->getLinkingEdge(edge->getSource());
        Edge *e2 = candidate->getLinkingEdge(edge->getTarget());

        if( ((e1!=NULL) && (e1->getType()!=1))
            || ((e2!=NULL) && (e2->getType()!=1)))
        {
            edge->setType(0);
            m_border_edges.push_back(edge);
            continue;
        }
        //checking that the front remains inside the given node and a small
        // band around it
        if(! containment_node->isInside(*candidate, d))
        {
            edge->setType(1);
            m_node_border_edges.push_back(edge);
            continue;
        }

        Facet * facet = new Facet(edge, candidate, center);
        addFacet(facet);

        e1 = candidate->getLinkingEdge(edge->getSource());
        e2 = candidate->getLinkingEdge(edge->getTarget());

        if(e1->getType() == 1)
            m_edge_front.push_front(e1);

        if(e2->getType() == 1)
            m_edge_front.push_front(e2);
    }
}


void Mesher::collectActiveEdges(OctreeNode* containment_node,
                                Edge_set &active_edges)
{
    if(containment_node->getDepth() != 0)
    {
        for(unsigned int i = 0; i <8; ++i)
        {
            if(containment_node->getChild(i) != NULL)
                collectActiveEdges(containment_node->getChild(i),active_edges);
        }
    }
    else
    {
        Vertex_list::iterator vi;
        for(vi = containment_node->points_begin();
            vi != containment_node->points_end(); ++vi)
            {
                if(vi->getType() != 1)
                    continue;

                Edge_set &edges = vi->adjacentEdges();
                Edge_set::iterator ei;
                for(ei = edges.begin(); ei != edges.end(); ++ei)
                {
                    Edge *e= *ei;
                    if(e->getType() == 1)
                        active_edges.insert(*ei);
                }
            }
    }
}


void Mesher::collectBorderEdges(OctreeNode *containment_node)
{
    Edge_set border_edges;
    collectBorderEdges(containment_node, border_edges);
    m_border_edges.insert(m_border_edges.end(), border_edges.begin(),
                          border_edges.end());
}

void Mesher::collectBorderEdges(OctreeNode* containment_node,
                                Edge_set& border_edges)
{
    if(containment_node->getDepth() != 0)
    {
        for(unsigned int i = 0; i <8; ++i)
        {
            if(containment_node->getChild(i) != NULL)
                collectBorderEdges(containment_node->getChild(i),border_edges);
        }
    }
    else
    {
        Vertex_list::iterator vi;
        for(vi = containment_node->points_begin();
            vi != containment_node->points_end(); ++vi)
            {
                if(vi->getType() != 1)
                    continue;

                Edge_set &edges = vi->adjacentEdges();
                Edge_set::iterator ei;
                for(ei = edges.begin(); ei != edges.end(); ++ei)
                {
                    Edge *e= *ei;
                    if(e->getType() == 0)
                        border_edges.insert(*ei);
                }
            }
    }
}




void Mesher::merge(Mesher& mesher)
{
    //merging the sets of facets
    m_facets.splice(m_facets.end(), mesher.m_facets);

    Edge_star_list::iterator ei = m_edge_front.begin();
    //merging the edge fronts
    while( ei != m_edge_front.end())
    {
        if((*ei)->getType() == 2)
        {
            ei = m_edge_front.erase(ei);
            continue;
        }

        else if((*ei)->getType() == 1)
        {
            ++ei;
        }

        else if((*ei)->getType() == 0)
        {
            ei = m_edge_front.erase(ei);
            continue;
        }
    }

    //merging the sets of vertices and renumbering them
    Vertex_star_list::iterator vi;
    for(vi = mesher.m_vertices.begin(); vi != mesher.m_vertices.end(); ++vi)
    {
        Vertex *v = *vi;
        unsigned int index = v->index();
        v->setIndex(index + m_nvertices);
        m_vertices.push_back(v);
    }

    //adding the node border edges (edges that could not be expanded due
    //to spatial containment) and add them to the front
    for(ei = mesher.m_node_border_edges.begin();
        ei != mesher.m_node_border_edges.end() ; ++ei)
        {
            m_edge_front.push_back(*ei);
        }
        mesher.m_node_border_edges.clear();

    //get the border edges and add it to the global mesher
    for(ei = mesher.m_border_edges.begin();
        ei != mesher.m_border_edges.end() ; ++ei)
        {
            if((*ei)->getFacet2()!=NULL)
            {
                continue;
            }
            m_border_edges.push_back(*ei);
        }
        mesher.m_border_edges.clear();

    m_nfacets = m_facets.size();
    m_nvertices = m_vertices.size();
}


