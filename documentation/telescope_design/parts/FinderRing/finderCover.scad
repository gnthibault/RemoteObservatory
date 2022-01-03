// Top cover for Evoguide 50 ED


// Global resolution
$fs = 0.1;  // Don't generate smaller facets than 0.1 mm
//$fa = 5;    // Don't generate larger angles than 0.5 degrees
$fn=120;      // DOn't generate more than n faces for a 360deg circle

// main geometry parameters
$m3_radius = 2.95/2;
$bar_width = 7.5;
$bar_depth = 5;

// define first arm
$attach_start_to_opening = 21;
$attach_start_to_first_m3_center = 8.9;
$attach_start_to_second_m3_center = $attach_start_to_first_m3_center+4.1;

// define disk holder
$center_arm_to_center_disk = 63;
$center_bar_to_start_disk = $bar_depth/2+1;

//define disk
$exactouterdiameter = 59.8;
$outerdiameter = $exactouterdiameter +2;
$cap_thickness = 1.6;
$start_outer_disk_to_end_bar=$bar_depth/2+3.8;

// protection cap
$height_protection_cap = $bar_width;
$thickness_protection_cap = 1.2;
$protection_outerdiameter = $outerdiameter + 2;

// Main geometry
//m3_hole();
//main_attach_bar();
//servo_attach();
//disk_support();
//top_cylinder();
//colerette();
//ring_link();

union() {
    servo_attach();
    disk_support();
    top_cylinder();
    colerette();
    ring_link();
}

module servo_attach() {
    difference() {
        difference() {
            main_attach_bar();
            translate([$attach_start_to_first_m3_center,0,0]) m3_hole();
        };
        translate([$attach_start_to_second_m3_center,0,0]) m3_hole();
    }
}

module main_attach_bar() {
    $attach_length = $attach_start_to_opening+$bar_width;
    color("Lime") translate([$attach_length/2,0,0]) cube([ 
        $attach_length,
        $bar_width,
        $bar_depth], center=true);
}

module m3_hole() {
    color("Black") cylinder(h=20, r=$m3_radius, center=true);
}

module disk_support() {
    $support_length = $center_arm_to_center_disk+$bar_width/2;
    $startx=$attach_start_to_opening+$bar_width/2;
    $starty=($support_length/2)-$bar_width/2;
    color("Cyan") translate([$startx,$starty,0]) cube([ 
        $bar_width,
        $support_length,
        $bar_depth], center=true);
}

module top_cylinder() {
    $shiftx=$attach_start_to_opening+$bar_width-$cap_thickness/2;
    $shiftz = $start_outer_disk_to_end_bar+$outerdiameter/2;
    color("Orchid") translate([$shiftx,$center_arm_to_center_disk,$shiftz]) rotate([0,90,0]) cylinder(
        h=$cap_thickness,
        r=$outerdiameter/2,
        center=true);
}

module colerette() {
    $shiftx=$attach_start_to_opening+$bar_width-$cap_thickness*3;
    $shiftz = $start_outer_disk_to_end_bar+$outerdiameter/2;
    translate([$shiftx,$center_arm_to_center_disk,$shiftz]) rotate([0,-90,0])
    difference() {
        cylinder(
            h=$height_protection_cap,
            r1=$outerdiameter/2,
            r2=$protection_outerdiameter/2,
            center=true);
        translate([0,0,$thickness_protection_cap]) cylinder(
            h=$height_protection_cap,
            r1=$outerdiameter/2-$thickness_protection_cap,
            r2=$protection_outerdiameter/2-$thickness_protection_cap,
            center=true);
    }
}

module ring_link() {
    $length = 25;
    $width = 14;
    $support_length = $center_arm_to_center_disk+$bar_width/2;
    $startx=$attach_start_to_opening+$bar_width/2;
    $starty=($support_length/2)-$bar_width/2 + $support_length/2;
    $startz = $width/2-$bar_depth/2;
    difference() {
        color("Gold") translate([$startx,$starty,$startz]) cube([ 
            $bar_width,
            $length,
            $width], center=true);
        protection_hole();
    }
}

module protection_hole() {
    $shiftx=$attach_start_to_opening+$bar_width-$cap_thickness*3;
    $shiftz = $start_outer_disk_to_end_bar+$outerdiameter/2;
    translate([$shiftx,$center_arm_to_center_disk,$shiftz]) rotate([0,-90,0])
    translate([0,0,$thickness_protection_cap]) cylinder(
    h=$height_protection_cap,
    r1=$outerdiameter/2-$thickness_protection_cap,
    r2=$protection_outerdiameter/2-$thickness_protection_cap,
    center=true);
}
