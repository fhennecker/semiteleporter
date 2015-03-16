/** @file FileIO.h
 * @brief file declaring methods to read points from a file
 * @author Julie Digne julie.digne@liris.cnrs.fr
 * @date 2012/10/22
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

#ifndef FILEIO_H
#define FILEIO_H

#include <fstream>
#include <iostream>

#include "Octree.h"
#include "Mesher.h"

#include "types.h"


/**
 * @class FileIO
 * @brief class providing access to input/output operations
 *
 * This class defines methods for reading points from an input file
 * and saving the resulting mesh in a ply file.
 */
class FileIO
{
    public :

        /** @brief constructor*/
        FileIO();

        /** @brief destructor*/
        ~FileIO();

    public :

        /** @brief read points from a file
         * @param filename name of the file to read points from
         * @param octree to sort and store the points in
         * @param min_radius if positive, create the octree such that
         * the smallest cell has size 2*min_radius
         * @return false if the file could not be opened
         */
        static bool readAndSortPoints(const char *filename, Octree &octree,
                                      double min_radius = -1);

        /** @brief save points from an octree to a file
         * @param filename name of the file to save to
         * @param octree octree to save the points from
         * @return false if something went wrong
         */
        static bool savePoints(const char* filename, Octree &octree);


        /** @brief save triangulation
         * @param filename name of the file to save to
         * @param mesher name of the mesher to save vertices and facets from
         * @return false if something went wrong
         */
        static bool saveMesh(const char* filename, Mesher &mesher);

    private :

        /** @brief save all vertices contained in a node
         * @param node node to save from
         * @param f stream to save to
         */
        static void saveContent(OctreeNode *node, std::ofstream &f);

};


#endif
