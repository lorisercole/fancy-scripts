#
# calculate the g(r) between all the types listed in typelist
#
# example usage, in vmd:
#
# source generate_gr.tcl
# ::gofrall::setMolId 1
# ::gofrall::calc 1 fileout.out { 1 2 3 4 5}
#

package provide gofr_all 1.0

#namespace delete ::gofrall

namespace eval ::gofrall {

        namespace export calc setMolId
        variable molId
}


proc ::gofrall::setMolId {id } {
        variable molId
        set molId $id
}

proc ::gofrall::calc { step outf typelist } {

        variable molId	

        set fileId [ open $outf w 0650 ]
        set gofr_all [list {} ]
        set gofr_int_all [list ]
        for {set i 0} {$i < [llength $typelist]} {incr i} { 
                for {set j 0 } {$j < [llength $typelist]} {incr j} {
                         set type1 [ lindex $typelist $i ]
                         set type2 [ lindex $typelist $j ]
                         set sel1 [ atomselect $molId "type $type1"]
                         set sel2 [ atomselect $molId "type $type2"]
                         set gofr [ measure gofr $sel1 $sel2 delta 0.05 rmax 10.0 usepbc true first 0 last -1 step $step ]
                         lappend gofr_int_all [ lindex $gofr 2 ]
                         lappend gofr_all [ lindex $gofr 1 ]
                }
        }
        for {set n 0} {$n < [llength [ lindex $gofr_all 1 ] ]} {incr n} {
                for {set i 0} {$i < [expr {[llength $typelist] * ([llength $typelist] ) } ]} {incr i} {
                         puts -nonewline $fileId "[lindex $gofr_int_all $i $n ] "
                }
                puts $fileId ""
        }


        close $fileId

}


proc ::gofrall::calc2 { step outf typelist } {

        variable molId	

        set fileId [ open $outf w 0650 ]
        set gofr_all [list {} ]
        set gofr_int_all [list ]
        for {set i 0} {$i < [llength $typelist]} {incr i} { 
                for {set j [expr {$i + 1}] } {$j < [llength $typelist]} {incr j} {
                         set type1 [ lindex $typelist $i ]
                         set type2 [ lindex $typelist $j ]
                         set sel1 [ atomselect $molId "type $type1"]
                         set sel2 [ atomselect $molId "type $type2"]
                         set gofr [ measure gofr $sel1 $sel2 delta 0.05 rmax 10.0 usepbc true first 0 last -1 step $step ]
                         lappend gofr_int_all [ lindex $gofr 2 ]
                         lappend gofr_all [ lindex $gofr 1 ]
                }
        }
        for {set n 0} {$n < [llength [ lindex $gofr_all 1 ] ]} {incr n} {
                for {set i 0} {$i < [expr {[llength $typelist] * ([llength $typelist] -1) / 2 } ]} {incr i} {
                         puts -nonewline $fileId "[lindex $gofr_int_all $i $n ] "
                }
                puts $fileId ""
        }


        close $fileId

}

