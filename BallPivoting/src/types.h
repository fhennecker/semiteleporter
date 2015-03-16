/**
 *@file types.h
 * @author Julie Digne
 * @brief Type definitions
 * @date 2012/10/25
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


#ifndef TYPES_H
#define TYPES_H

#include<list>
#include<set>
#include<map>
#include "Point.h"

class Vertex;
class Edge;
class Facet;

typedef std::list<Point> Point_list;
typedef std::list<Point*> Point_star_list;
typedef std::list<double> Distance_list;
typedef std::list<Point>::iterator Point_iterator;
typedef std::list<Point*>::iterator Point_star_iterator;
typedef std::set<Edge*> Edge_set;
typedef std::set<Facet*> Facet_set;


typedef std::list<Vertex> Vertex_list;
typedef std::list<Vertex>::iterator  Vertex_iterator;
typedef std::list<Vertex*> Vertex_star_list;
typedef std::list<Vertex*>::iterator Vertex_star_iterator;

typedef std::list<Edge> Edge_list;
typedef std::list<Edge>::iterator  Edge_iterator;
typedef std::list<Edge*> Edge_star_list;
typedef std::list<Edge*>::iterator Edge_star_iterator;

typedef std::list<Facet> Facet_list;
typedef std::list<Facet>::iterator  Facet_iterator;
typedef std::list<Facet*> Facet_star_list;
typedef std::list<Facet*>::iterator Facet_star_iterator;

typedef std::map<double, Vertex*> Neighbor_star_map;
typedef Neighbor_star_map::iterator Neighbor_iterator;

#include "Octree.h"
typedef TOctree<Vertex> Octree;

#include "OctreeNode.h"
typedef TOctreeNode<Vertex> OctreeNode;
typedef std::vector<OctreeNode*> OctreeNode_vector;
typedef std::vector<OctreeNode_vector> OctreeNode_collection;


#include "OctreeIterator.h"
typedef TOctreeIterator<Vertex> OctreeIterator;


#endif