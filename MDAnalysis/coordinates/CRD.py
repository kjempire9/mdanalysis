# $Id: CRD.py 101 2009-08-11 13:19:06Z denniej0 $
"""CRD structure files in MDAnalysis

Only coordinates are written at the moment.

VERY Primative CRD generator (may still have to be debugged!)

 It may need some debugging (i.e.-it might not work for large systems
 as they usually need the extended version of crd writing).

"""

import MDAnalysis
import MDAnalysis.core.util as util
import base
from MDAnalysis import FormatError
import numpy
from base import Timestep


class CRDReader(base.Reader):
    """CRD reader that implements the standard and extended CRD coordinate formats
    """
    format = 'CRD'
    units = {'time': None, 'length': 'nm'}
    _Timestep = Timestep
 
    def __init__(self, crdfilename, convert_units=None):
        self.crdfilename = crdfilename
        self.filename = self.crdfilename
        if convert_units is None:
            convert_units = MDAnalysis.core.flags['convert_gromacs_lengths']
        self.convert_units = convert_units  # convert length and time to base units

	coords_list = []
        crdfile = open(crdfilename , 'r').readlines()
        
        for linenum,line in enumerate(crdfile):
	   if line.split()[0] == '*':
               continue 
               #print line.split()[0]
	   elif line.split()[-1] == 'EXT' and bool(int(line.split()[0])) == True: 
	       extended = 'yes'
           elif line.split()[0] == line.split()[-1] and line.split()[0] != '*':
	       extended = 'no' 
	   elif extended == 'yes':
               coords_list.append( numpy.array( map( float , line[45:100].split()[0:3] ) ) )
	   elif extended == 'no':
               coords_list.append( numpy.array( map( float , line[20:50].split()[0:3] ) ) )
           else:
               raise FormatError("Check CRD format at line %d: %s" % (linenum, line.rstrip()))

	self.numatoms = len(coords_list)
	coords_list = numpy.array(coords_list)
        self.numframes = 1
        self.fixed = 0          # parse B field for fixed atoms?
        self.skip = 1
        self.periodic = False
        self.delta = 0
        self.skip_timestep = 1
        self.ts = self._Timestep(coords_list)

    def __len__(self):
        return self.numframes
    def __iter__(self):
        yield self.ts  # Just a single frame
        raise StopIteration
    def __getitem__(self, frame):
        if frame != 0:
            raise IndexError('PrimitivePDBReader can only read a single frame at index 0')
        return self.ts
    def _read_next_timestep(self):
        raise IndexError("PrimitivePDBReader can only read a single frame")

class CRDWriter(base.Writer):
    """CRD writer that implements the CHARMM CRD coordinate format.

    It automatically writes the CHARMM EXT extended format if there
    are more than 99,999 atoms.
    """
    format = 'CRD'
    units = {'time': None, 'length': 'Angstrom'}

    fmt = {
        #crdtype = 'extended'
        #fortran_format = '(2I10,2X,A8,2X,A8,3F20.10,2X,A8,2X,A8,F20.10)'
        'ATOM_EXT':"%(serial)10d%(TotRes)10d  %(resName)-8s  %(name)-8s%(x)20.10f%(y)20.10f%(z)20.10f  %(chainID)-8s  %(resSeq)-8d%(tempFactor)20.10f\n",
        'NUMATOMS_EXT':"%10d  EXT\n",
        #crdtype = 'standard'
        #fortran_format = '(2I5,1X,A4,1X,A4,3F10.5,1X,A4,1X,A4,F10.5)'
        'ATOM':"%(serial)5d%(TotRes)5d %(resName)-4s %(name)-4s%(x)10.5f%(y)10.5f%(z)10.5f %(chainID)-4s %(resSeq)-4d%(tempFactor)10.5f\n",
        'TITLE':  "*%s\n",
        'NUMATOMS':"%5d\n",
        }

    def __init__(self,filename,**kwargs):
        self.filename = util.filename(filename,ext='crd')
        self.crd = None

    def close_trajectory(self):
        pass

    def write(self,selection,frame=None):
        """Write selection at current trajectory frame to file.

        write(selection,frame=FRAME)

        selection         MDAnalysis AtomGroup
        frame             optionally move to frame FRAME
        """
        u = selection.universe
        if frame is not None:            
            u.trajectory[frame]  # advance to frame
        else:
            try:
                frame = u.trajectory.ts.frame
            except AttributeError:
                frame = 1   # should catch cases when we are analyzing a single PDB (?)
       
        atoms = selection.atoms     # make sure to use atoms (Issue 46)
        coor = atoms.coordinates()  # can write from selection == Universe (Issue 49)
        self.crd = open(self.filename,'w')
        try:
            self._TITLE("FRAME "+str(frame)+" FROM "+str(u.trajectory.filename))
            self._TITLE("")
            self._NUMATOMS(len(atoms))
            current_resid = 0
            for i, atom in enumerate(atoms):
                if atoms[i].resid != atoms[i-1].resid:
                    # note that this compares first and LAST atom on first iteration... but it works
                    current_resid += 1
                self._ATOM(serial=i+1, resSeq=atom.resid, resName=atom.resname, name=atom.name,
                          x=coor[i,0], y=coor[i,1], z=coor[i,2], chainID=atom.segid,tempFactor=0.0,TotRes=current_resid,numatoms=len(atoms))
                # get bfactor, too?
        finally:
            self.crd.close()

    def _TITLE(self,*title):
        """Write TITLE record.
        """        
        line = " ".join(title)    # should do continuation automatically
        line = line.strip()
        if len(line) > 0:
            line = " "+line
        self.crd.write(self.fmt['TITLE'] % line)

    def _NUMATOMS(self,numatoms):
	"""Write generic total number of atoms in system)
	"""
        if numatoms > 99999:
	    self.crd.write(self.fmt['NUMATOMS_EXT'] % numatoms) 
        else: 
            self.crd.write(self.fmt['NUMATOMS'] % numatoms)
    
    def _ATOM(self,serial=None,resSeq=None,resName=None,name=None,x=None,y=None,z=None,chainID=None,tempFactor=0.0,TotRes=None,numatoms=None):
        """Write ATOM record. 

        All inputs are cut to the maximum allowed length. For integer
        numbers the highest-value digits are chopped (so that the
        serial and reSeq wrap); for strings the trailing characters
        are chopped.

        Note: Floats are not checked and can potentially screw up the format.
        """
        for arg in ('serial','name','resName','resSeq','x','y','z','tempFactor'):
            if locals()[arg] is None:
                raise ValueError('parameter '+arg+' must be defined.')

        chainID = chainID or ""   # or should we provide a chainID such as 'A'?
        if numatoms > 99999:
            serial = int(str(serial)[-10:])  # check for overflow here?
            name = name[:8]
            resName = resName[:8]
            chainID = chainID[:8]
            resSeq = int(str(resSeq)[-8:]) # check for overflow here?
            TotRes = int(str(TotRes)[-10:])
	    self.crd.write(self.fmt['ATOM_EXT'] % vars())
        else:
            serial = int(str(serial)[-5:])  # check for overflow here?
            name = name[:4]
            resName = resName[:4]
            chainID = chainID[:4]
            resSeq = int(str(resSeq)[-4:]) # check for overflow here?
            TotRes = int(str(TotRes)[-5:])
	    self.crd.write(self.fmt['ATOM'] % vars())

