import { useMutation, useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Button } from "./ui/button";
import { Label } from "./ui/label";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";
import { Slider } from "./ui/slider";
import { useEffect, useState } from "react";

export const Settings = () => {
    const userSettings = useQuery(api.users.getUserSettings);
    const updateUserSettings = useMutation(api.users.updateUserSettings);

    const [headerFont, setHeaderFont] = useState("PP Editorial");
    const [bodyFont, setBodyFont] = useState("Geist");
    const [theme, setTheme] = useState("light");
    const [randomnessTemperature, setRandomnessTemperature] = useState(1);

    useEffect(() => {
        if (userSettings) {
            setHeaderFont(userSettings.headerFont ?? "PP Editorial");
            setBodyFont(userSettings.bodyFont ?? "Geist");
            setTheme(userSettings.theme ?? "light");
            setRandomnessTemperature(userSettings.randomnessTemperature ?? 1);
        }
    }, [userSettings]);

    const handleSave = () => {
        updateUserSettings({
            headerFont,
            bodyFont,
            theme,
            randomnessTemperature,
        });
    };

    return (
        <div className="space-y-8">
            <div>
                <Label>Header Font</Label>
                <RadioGroup value={headerFont} onValueChange={setHeaderFont}>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="PP Editorial" id="pp-editorial" />
                        <Label htmlFor="pp-editorial">PP Editorial (Serif)</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="Geist" id="geist-header" />
                        <Label htmlFor="geist-header">Geist (Sans Serif)</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="monospace" id="monospace-header" />
                        <Label htmlFor="monospace-header">Monospace</Label>
                    </div>
                </RadioGroup>
            </div>
            <div>
                <Label>Body Font</Label>
                <RadioGroup value={bodyFont} onValueChange={setBodyFont}>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="Geist" id="geist-body" />
                        <Label htmlFor="geist-body">Geist (Sans Serif)</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="PP Editorial" id="pp-editorial-body" />
                        <Label htmlFor="pp-editorial-body">PP Editorial (Serif)</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="monospace" id="monospace-body" />
                        <Label htmlFor="monospace-body">Monospace</Label>
                    </div>
                </RadioGroup>
            </div>
            <div>
                <Label>Theme</Label>
                <RadioGroup value={theme} onValueChange={setTheme}>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="light" id="light" />
                        <Label htmlFor="light">Light</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="dark" id="dark" />
                        <Label htmlFor="dark">Dark</Label>
                    </div>
                </RadioGroup>
            </div>
            <div>
                <Label>Randomness Temperature</Label>
                <Slider
                    value={[randomnessTemperature]}
                    onValueChange={(value) => setRandomnessTemperature(value[0])}
                    min={0}
                    max={10}
                    step={0.1}
                />
            </div>
            <Button onClick={handleSave}>Save</Button>
        </div>
    );
};
