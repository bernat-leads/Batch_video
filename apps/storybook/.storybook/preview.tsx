import { Toaster } from '@packages/ui/components/shadcn/sonner';
import { TooltipProvider } from '@packages/ui/components/shadcn/tooltip';
import { ThemeProvider } from '@packages/ui/providers/theme';
import type { Preview } from '@storybook/react';
import React from 'react';

import '@packages/ui/styles/global';

const preview: Preview = {
  decorators: [
    Story => {
      return (
        <div className="bg-background">
          <ThemeProvider>
            <TooltipProvider>
              <Story />
            </TooltipProvider>
            <Toaster />
          </ThemeProvider>
        </div>
      );
    },
  ],
};

export default preview;
