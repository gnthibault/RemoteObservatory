// First end to end project
maindustcapplate();

module maindustcapplate()
{
    mainplatethickness = 3;
    tubediameter = 255;
    mainplatediameter = tubediameter+2*mainplatethickness;
    elpaneldiameter = 250;
    colerettelength = 20;
    colerettethickness = mainplatethickness;
    coleretteangledegree = 10;
    cablepassthroughdiameter  = 2;
    supportspacing = 50;
    supportlengthinplate = tubediameter*0.67;
    supportlengthoutofplate = 50;
    
    // define main plate base
    mainplate( internaldiameter=mainplatediameter, thickness=mainplatethickness);
    
    // define collerette
    colerette(internaldiameter=mainplatediameter, thickness=colerettethickness, length=colerettelength, angledegree=coleretteangledegree);
    
    // supporting arm
    //supportingarm()
}


module mainplate(internaldiameter, thickness)
{
    // define main plate base
    cylinder( r=internaldiameter/2, h=thickness, center=false);
}


module colerette(internaldiameter, thickness, length, angledegree)
{
    internalradius = internaldiameter/2;
    internaradius2 = internalradius+length*tan(angledegree);
    
    externalradius = (internaldiameter+thickness)/2;
    externalradius2 = internaradius2+thickness;
    
    heihtatorigin = length*0.9;
    cutangle = 3;

    difference()
    {
        // external
        cylinder(r1=externalradius, r2=externalradius2, h=length, center=false);
        // internal
        cylinder(r1=internalradius, r2=internaradius2, h=length, center=false);
        //cylinder(r=1, h=1, center=false);
        //cylinder(r=1, h=1, center=false);
        translate([0,0,heihtatorigin]) rotate([0,cutangle,0]) cylinder(r=externalradius2/cos(cutangle), h=length/cos(cutangle));
    }
}