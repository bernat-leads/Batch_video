import { cn } from "../../lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "./avatar";
import { Card, CardContent } from "./card";

interface TestimonialCardProps {
  content: string;
  author: {
    name: string;
    role: string;
    company: string;
    avatar?: string;
  };
  rating?: number;
  className?: string;
  variant?: "default" | "highlighted" | "minimal";
}

export function TestimonialCard({
  content,
  author,
  rating = 5,
  className,
  variant = "default",
}: TestimonialCardProps) {
  const getVariantClasses = () => {
    switch (variant) {
      case "highlighted":
        return "border-blue-500/20 bg-gradient-to-br from-blue-50/50 to-purple-50/50 dark:from-blue-950/20 dark:to-purple-950/20 shadow-lg shadow-blue-500/10";
      case "minimal":
        return "border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950";
      default:
        return "border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950 shadow-sm hover:shadow-md transition-shadow duration-300";
    }
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <svg
        key={i}
        className={cn(
          "h-4 w-4",
          i < rating ? "fill-current text-yellow-400" : "text-gray-300 dark:text-gray-600"
        )}
        viewBox="0 0 20 20"
      >
        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
      </svg>
    ));
  };

  return (
    <Card className={cn("h-full", getVariantClasses(), className)}>
      <CardContent className="p-6">
        {rating && <div className="mb-4 flex items-center gap-1">{renderStars(rating)}</div>}

        <blockquote className="mb-6 leading-relaxed text-gray-700 italic dark:text-gray-300">
          "{content}"
        </blockquote>

        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10">
            <AvatarImage src={author.avatar} alt={author.name} />
            <AvatarFallback className="bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400">
              {author.name
                .split(" ")
                .map(n => n[0])
                .join("")}
            </AvatarFallback>
          </Avatar>

          <div className="flex flex-col">
            <div className="font-semibold text-gray-900 dark:text-gray-100">{author.name}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {author.role} at {author.company}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
